import type { Metadata } from "next";
import { Widget } from "@/components/Widget";

export const metadata: Metadata = { title: "FRA Runway Outlook · Widget" };

export default function WidgetPage() {
  return <Widget />;
}
