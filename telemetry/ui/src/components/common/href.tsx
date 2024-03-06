/**
 * Simple component to display text as a link
 * Meant to be used consistently
 */
export const LinkText = (props: { href: string; text: string }) => {
  return (
    <a
      href={props.href}
      className="text-dwlightblue hover:underline"
      onClick={(e) => {
        // Quick trick to ensure that this takes priority and if this has a parent href, it doesn't trigger
        e.stopPropagation();
      }}
    >
      {props.text}
    </a>
  );
};
