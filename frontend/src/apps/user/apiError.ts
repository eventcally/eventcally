import { toFieldErrors, type FieldErrorItem } from "@/shared/fieldErrors";

/** The `message` of an error answer, or the fallback (network errors have none). */
export function errorMessage(error: unknown, fallback: string): string {
  const message = (error as { message?: string } | undefined)?.message;
  return message || fallback;
}

/** The field errors of a 422 answer mapped onto the form's fields; null for other errors. */
export function mapFieldErrors(error: unknown, known: string[]) {
  if (error && typeof error === "object" && "errors" in error) {
    return toFieldErrors((error as { errors: FieldErrorItem[] }).errors, known);
  }
  return null;
}
