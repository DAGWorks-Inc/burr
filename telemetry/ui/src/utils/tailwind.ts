export const classNames = (...classes: string[]): string => {
  return classes.filter(Boolean).join(' ');
};
