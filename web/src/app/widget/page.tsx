import type { Metadata } from "next";
import { Widget } from "@/components/Widget";

export const metadata: Metadata = { title: "Liftoff · iPad widget" };

export default function WidgetPage() {
  return <Widget />;
}
