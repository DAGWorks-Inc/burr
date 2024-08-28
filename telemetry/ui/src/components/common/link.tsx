/**
 * Tailwind catalyst component
 *
 * This is an abstraction of a link -- we'll need to
 * ensure this does what we want.
 */

import { Link as RouterLink } from 'react-router-dom';
import React from 'react';

export const Link = React.forwardRef(function Link(
  props: { href: string } & React.ComponentPropsWithoutRef<'a'>,
  ref: React.ForwardedRef<HTMLAnchorElement>
) {
  return (
    <RouterLink {...props} to={props.href} ref={ref} />
    // <HeadlessDataInteractive>
    //   <a {...props} ref={ref} />
    // </HeadlessDataInteractive>
  );
});
