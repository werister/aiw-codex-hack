import Image from "next/image";
import "./BrandLogo.css";

export function BrandLogo() {
  return (
    <span className="lift-off-logo">
      <Image
        src="/brand/lift-off-compass.png"
        alt="Lift-off"
        width={2172}
        height={724}
        loading="eager"
        unoptimized
        className="lift-off-logo__image"
      />
    </span>
  );
}
