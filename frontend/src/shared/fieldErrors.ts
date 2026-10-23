export interface FieldErrorItem {
  loc: string[];
  msg: string;
}

export interface MappedFieldErrors {
  /** Error messages by dotted location, e.g. `location.city`. */
  byKey: Record<string, string>;
  /** Messages whose location is not one of the form's fields. */
  unmatched: string[];
}

/** Maps the `errors` of a 422 onto the dotted keys of the fields a form actually shows. */
export function toFieldErrors(errors: FieldErrorItem[], known: string[]): MappedFieldErrors {
  const byKey: Record<string, string> = {};
  const unmatched: string[] = [];

  for (const error of errors) {
    const key = error.loc.join(".");
    if (known.includes(key)) byKey[key] ??= error.msg;
    else unmatched.push(error.msg);
  }

  return { byKey, unmatched };
}
