import { BrandLogo } from "./BrandLogo";

export function Brand({ subtitle }: { subtitle?: string }) {
  return (
    <div className="flex min-w-0 items-center gap-4">
      <h1 className="shrink-0"><BrandLogo /></h1>
      {subtitle && <span className="hidden truncate text-[15px] text-muted sm:inline">{subtitle}</span>}
    </div>
  );
}
