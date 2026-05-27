import { redirect } from "next/navigation";

export default async function GoalRoute({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const instruction = typeof sp.instruction === "string" ? sp.instruction : "";
  const founder = typeof sp.founder === "string" ? sp.founder : "";
  const company = typeof sp.company === "string" ? sp.company : "";

  const query = new URLSearchParams({ session: id });
  if (instruction) query.set("instruction", instruction);
  if (founder) query.set("founder", founder);
  if (company) query.set("company", company);

  redirect(`/?${query.toString()}`);
}
