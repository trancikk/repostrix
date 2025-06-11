export function parseNumber(num: string | null | undefined | number | unknown) {
  if (typeof num === "number") {
    return num;
  } else if (typeof num === "string") {
    const parsedNumber = parseInt(num);
    if (!isNaN(parsedNumber)) {
      return parsedNumber;
    }
  }
  return null;
}
