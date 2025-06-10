export function isKilometerExpenseType(expenseTypeName: string): boolean {
  const kilometerTypes = ["fahrkilometer", "kilometer"];
  return kilometerTypes.some((type) => expenseTypeName.toLowerCase().includes(type));
}

export function getExpenseUnit(expenseTypeName: string): string {
  return isKilometerExpenseType(expenseTypeName) ? "km" : "CHF";
}

export function formatExpenseAmount(amount: number, expenseTypeName: string): string {
  const unit = getExpenseUnit(expenseTypeName);
  return `${amount.toFixed(2)} ${unit}`;
}
