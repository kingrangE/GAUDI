# PostgreSQL 데이터 보호 — 월 $20 포트폴리오 배포

이번 구성은 **앱 서버와 DB 서버를 분리**하는 배포의 DB 부분이다. AWS 리소스를
자동 생성하지 않는다. 일반 EC2의 요금에는 EBS·IPv4가 별도이며, 서버 두 대·백업·세금을
합쳐 $20 안에 들어가는지는 배포 전에 서울 리전 견적을 확인한다. Lightsail을 선택하면
아래 instance role 대신 제한된 IAM 자격 증명의 안전한 제공 방법도 별도로 결정한다.
LLM 사용료와 코드 실행 격리는 이 예산/구현에 포함하지 않는다.

## 보장 범위

- PostgreSQL 17, 영속 Docker volume, 앱에는 superuser 대신 `gaudi_app` 제공.
- 매일 한국 시간 03시경 일관된 custom-format dump 생성 → 임시 DB에 실제 복원 →
  테이블 존재 확인 → S3 암호화 업로드. 실패하면 비정상 종료하고 SNS 알림.
- S3에서 내려받은 백업도 `verify`로 실제 복원 가능. 운영 DB를 덮어쓰는 인자는 없다.
- S3 버전 관리, public access 차단, HTTPS 강제, 현재 백업 14일 보관.
  만료된 버전은 추가 7일 후 삭제될 수 있어 실제 저장 기간은 14일보다 길다.
- **목표 RPO 약 24시간**: 일일 백업이 성공한 경우에만 해당한다. 실패가 이어지면
  마지막 성공 이후 변경분은 잃는다. RTO는 새 서버 재구축까지 직접 측정한다.
- PITR, 자동 failover, DB 역할/비밀번호 백업은 없다. 서버 전체가 사라지면 이 폴더와
  비밀번호 관리 도구에 보관한 비밀값으로 DB를 초기화하고 dump를 복원한다.

## 1. DB 서버 시작

Ubuntu LTS에 Docker Engine + Compose v2, Python 3, AWS CLI v2를 설치한다.
소스는 `/opt/gaudi`에 둔다. AWS CLI 경로는 `/usr/local/bin/aws`로 맞춘다.
서버는 암호화된 EBS를 사용하고, 루트 계정 MFA도 활성화한다.

```sh
cd /opt/gaudi/deploy/postgres
cp .env.example .env
chmod 600 .env
# .env의 두 비밀번호를 각각 길게 생성해 입력하고 DB_BIND_IP를 DB 서버 사설 IP로 설정
docker compose up -d --wait
```

`init-app.sql`은 **빈 volume에서 최초 시작할 때만** 실행된다. `.env` 변경만으로 기존
DB 비밀번호가 바뀌지 않는다. 기존 데이터가 있다면 먼저 백업하고 SQL로 비밀번호를
변경한다. `docker compose down -v`는 데이터를 지우므로 운영에서 사용하지 않는다.
`postgres:17-bookworm`의 minor 업데이트는 백업 확인 후 계획해서 적용하며,
major 버전은 이미지 태그만 바꿔 올리지 않는다.

EC2 보안 그룹은 TCP 5432 수신을 **앱 서버 보안 그룹에만** 허용한다. 앱과 DB는
같은 VPC에서 사설 IP로 통신한다. DB용 public IPv4는 필요하지 않지만, 패키지 업데이트와
S3/SNS 접근 경로는 필요하다. IPv6 외부 통신을 쓰거나, IPv4를 사용하면서 수신을 제한한다.
이 예산에서 NAT Gateway를 만들지 않는다. 프라이빗 IPv4만으로는 S3에 접속할 수 없다.
Lightsail은 같은 리전의 private network와 호스트 방화벽을 별도로 설정해야 한다.
Docker published port는 UFW 규칙을 우회할 수 있으므로 UFW만 믿고 공개하면 안 된다.

외부에서 5432 접속 실패, 앱 서버에서만 연결 성공하는지 실제로 확인한다.
SSH도 운영자 IP만 허용한다. DB 컨테이너에 LLM 키를 전달하지 않는다.

앱 서버의 `DATABASE_URL`:

```text
postgresql+asyncpg://gaudi_app:<URL-encoded APP_DB_PASSWORD>@<DB-private-IP>:5432/gaudi
```

## 2. S3와 실패 알림 설정

서울 리전에 백업 전용 S3 bucket과 SNS Standard topic을 생성하고 이메일 구독을
추가한 뒤 **구독 확인 메일을 승인**한다. 모든 S3 public access를 차단하고
versioning과 기본 SSE-S3 암호화를 활성화한다. bucket policy에는 아래의
HTTPS 강제 정책을 추가한다 (`BUCKET` 교체):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::BUCKET", "arn:aws:s3:::BUCKET/*"],
    "Condition": {"Bool": {"aws:SecureTransport": "false"}}
  }]
}
```

EC2에는 instance role을 연결하고 다음 최소 권한을 부여한다. 정적 AWS 키를
저장소나 `.env`에 넣지 않는다. `BUCKET`, `SNS_TOPIC_ARN`을 교체한다.
이 역할에는 백업 삭제, 버전 삭제, bucket 설정 변경 권한을 주지 않는다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::BUCKET/gaudi/postgres/*"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "SNS_TOPIC_ARN"
    }
  ]
}
```

운영자 자격 증명으로 전용 bucket에 lifecycle을 적용한다. 이 명령은 bucket의
기존 lifecycle 구성을 대체하므로 다른 용도의 bucket에 실행하지 않는다.

```sh
aws s3api put-bucket-lifecycle-configuration --bucket BUCKET \
  --lifecycle-configuration file://s3-lifecycle.json
```

`/etc/gaudi-backup.env`를 root 소유, 권한 `600`으로 작성한다:

```text
AWS_DEFAULT_REGION=ap-northeast-2
BACKUP_S3_PREFIX=s3://BUCKET/gaudi/postgres
BACKUP_ALERT_TOPIC_ARN=arn:aws:sns:ap-northeast-2:ACCOUNT:TOPIC
```

## 3. 수동 검증 후 타이머 활성화

앱 초기화로 테이블이 생성된 뒤 실행한다. 빈 DB는 검증 실패로 처리한다.

```sh
sudo cp gaudi-db-backup.service gaudi-db-backup.timer gaudi-db-backup-alert.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gaudi-db-backup.service
sudo journalctl -u gaudi-db-backup.service -n 30
# BACKUP_OK와 S3 객체 생성 확인

# 알림 서비스도 직접 실행하고 이메일 수신 확인
sudo systemctl start gaudi-db-backup-alert.service
sudo systemctl enable --now gaudi-db-backup.timer
systemctl list-timers gaudi-db-backup.timer
```

AWS CLI를 수동 실행할 때도 위 세 환경변수를 설정한다. 비밀번호는 Compose가
`.env`에서 읽으며 프로세스 인자에 전달하지 않는다.

```sh
export AWS_DEFAULT_REGION=ap-northeast-2
export BACKUP_S3_PREFIX=s3://BUCKET/gaudi/postgres
sudo --preserve-env=AWS_DEFAULT_REGION,BACKUP_S3_PREFIX \
  python3 backup.py verify s3://BUCKET/gaudi/postgres/EXACT-BACKUP-NAME.dump
```

백업/복구 검증은 같은 서버의 임시 DB를 사용하므로 DB 크기 이상의 추가 디스크와
실행 여유가 필요하다. 임시 파일은 `/tmp`에 생성되므로 여유 공간도 확인한다.
프로세스 강제 종료 시 `restore_check_...` DB가 남을 수 있다. 실행 중인 작업이 없음을
확인한 뒤 해당 임시 DB만 제거한다. 단일 명령 제한은 10분, 전체 백업은 30분이다.

## 4. 정기 확인 및 장애 복구

로컬 테스트 (저장소 루트, backend 개발 의존성 설치 후):

```sh
backend/.venv/bin/pytest backend/tests/test_database_backups.py
RUN_DB_BACKUP_TESTS=1 backend/.venv/bin/pytest backend/tests/test_database_backups.py
```

두 번째 명령은 별도 PostgreSQL 17 컨테이너와 임시 volume을 생성하고 종료 시 삭제한다.
실제 dump/restore·행 보존·운영 DB 비변경·손상 archive 거부를 검증하며,
S3 전송만 로컬 파일 복사로 대체한다. 기존 DB에는 접속하지 않는다.

- 주 1회 S3에서 최근 성공 객체의 날짜를 확인하고 그 URI로 `verify` 실행.
- 첫 배포와 스키마 변경 후에는 별도 서버에서 복원하고 앱의 결과 조회까지 확인.
- `journalctl --disk-usage`, `df -h`로 로그/디스크 사용량 확인. 알림 이메일 수신 확인.
- AWS 예산 알림은 $15와 $18에 설정. 자동 과금 차단은 아니다.
- shortcut: 실패 알림은 DB 호스트가 실행 중일 때만 전송된다. 호스트 전체 중단을
  자동 감지해야 할 때는 외부에서 마지막 S3 백업 시간을 감시하는 기능을 추가한다.

**실제 복구는 앱 쓰기를 중지하고 새 DB 서버에서 한다.** 운영 중인 DB에 덮어쓰지 않는다.

1. 새 서버에서 이 Compose와 새로운 비밀번호로 빈 DB를 생성한다.
2. 운영자 권한으로 S3의 복구할 dump를 다운로드한다. 먼저 `verify`로 검증한다.
3. 새 DB에만 아래 명령으로 복원한다. `--role=gaudi_app`으로 앱 객체 소유권도 복원한다.
4. 앱 서버에서 새 DB로 읽기/쓰기 및 실제 결과 조회를 확인하고 `DATABASE_URL`을 전환한다.
5. 새 서버에서 백업·알림·타이머를 다시 확인한다. 이전 DB는 검증 완료 전까지 보관한다.

```sh
docker compose exec -T --user postgres postgres pg_restore \
  -U postgres -d gaudi --role=gaudi_app --no-owner --no-acl \
  --single-transaction --exit-on-error < /secure/path/gaudi.dump
```

이 절차는 `gaudi_app`이 `public` 스키마를 소유하는 이 Compose 구성용이다.
dump는 신뢰하는 전용 bucket의 것만 사용한다. PostgreSQL 복원은 dump에 포함된 SQL을
실행하므로 임의로 제공받은 파일을 복원하지 않는다.

동작 근거: [PostgreSQL pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html),
[S3 lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html).
