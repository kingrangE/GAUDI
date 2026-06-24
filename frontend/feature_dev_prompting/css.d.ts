// Let tsc accept CSS-module imports (class map). Vitest mocks these at run time.
declare module "*.module.css" {
  const classes: Record<string, string>;
  export default classes;
}
