import type { Metadata } from "next";
import { PlayApp } from "@/components/play/PlayApp";

export const metadata: Metadata = { title: "Lift-off · Play the wind" };

export default function PlayPage() {
  return <PlayApp />;
}
