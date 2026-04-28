import { adminPath } from "@/lib/admin-path";
import { redirect } from "next/navigation";

export default function AdminRootPage() {
  redirect(adminPath("/settings"));
}
