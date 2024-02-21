/**
 * Simple component to display text as a link
 * Meant to be used consistently
 */
export const LinkText = (props: { href: string; text: string }) => {
  return (
    <a href={props.href} className="text-dwlightblue hover:underline">
      {props.text}
    </a>
  );
};
