import Image from "next/image";
import "./BrandLogo.css";

export function BrandLogo() {
  return (
    <span className="lift-off-logo">
      <Image
        src="/brand/lift-off-wordmark.png"
        alt="Lift-off"
        width={1882}
        height={836}
        loading="eager"
        unoptimized
        className="lift-off-logo__image"
      />
    </span>
  );
}
