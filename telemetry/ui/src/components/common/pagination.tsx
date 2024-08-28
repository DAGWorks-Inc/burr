import clsx from 'clsx';
import type React from 'react';
import { Button } from './button';

export function Pagination({
  'aria-label': ariaLabel = 'Page navigation',
  className,
  ...props
}: React.ComponentPropsWithoutRef<'nav'>) {
  return <nav aria-label={ariaLabel} {...props} className={clsx(className, 'flex gap-x-2')} />;
}

export function PaginationPrevious({
  href = null,
  className,
  children = 'Previous'
}: React.PropsWithChildren<{ href?: string | null; className?: string }>) {
  return (
    <span className={clsx(className, 'grow basis-0')}>
      <Button {...(href === null ? { disabled: true } : { href })} plain aria-label="Previous page">
        <svg
          className="stroke-current"
          data-slot="icon"
          viewBox="0 0 16 16"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M2.75 8H13.25M2.75 8L5.25 5.5M2.75 8L5.25 10.5"
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {children}
      </Button>
    </span>
  );
}

export function PaginationNext({
  href = null,
  className,
  children = 'Next'
}: React.PropsWithChildren<{ href?: string | null; className?: string }>) {
  return (
    <span className={clsx(className, 'flex grow basis-0 justify-end')}>
      <Button {...(href === null ? { disabled: true } : { href })} plain aria-label="Next page">
        {children}
        <svg
          className="stroke-current"
          data-slot="icon"
          viewBox="0 0 16 16"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M13.25 8L2.75 8M13.25 8L10.75 10.5M13.25 8L10.75 5.5"
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </Button>
    </span>
  );
}

export function PaginationList({ className, ...props }: React.ComponentPropsWithoutRef<'span'>) {
  return <span {...props} className={clsx(className, 'hidden items-baseline gap-x-2 sm:flex')} />;
}

export function PaginationPage({
  href,
  className,
  current = false,
  children
}: React.PropsWithChildren<{ href: string; className?: string; current?: boolean }>) {
  return (
    <Button
      href={href}
      plain
      aria-label={`Page ${children}`}
      aria-current={current ? 'page' : undefined}
      className={clsx(
        className,
        'min-w-[2.25rem] before:absolute before:-inset-px before:rounded-lg',
        current && 'before:bg-zinc-950/5 dark:before:bg-white/10'
      )}
    >
      <span className="-mx-0.5">{children}</span>
    </Button>
  );
}

export function PaginationGap({
  className,
  children = <>&hellip;</>,
  ...props
}: React.ComponentPropsWithoutRef<'span'>) {
  return (
    <span
      aria-hidden="true"
      {...props}
      className={clsx(
        className,
        'w-[2.25rem] select-none text-center text-sm/6 font-semibold text-zinc-950 dark:text-white'
      )}
    >
      {children}
    </span>
  );
}
export const Paginator = (props: {
  currentPage: number;
  getPageURL: (page: number) => string;
  totalPages: number | undefined; // undefined if total pages is unknown
  hasNextPage: boolean;
}) => {
  const { currentPage, getPageURL, totalPages } = props;

  const renderPageNumbers = () => {
    const pages = [];

    if (totalPages !== undefined) {
      for (let page = currentPage - 2; page <= currentPage + 2; page++) {
        const classNames = page < 1 || page > totalPages ? 'invisible' : '';
        // TODO -- add pagination gap
        pages.push(
          <PaginationPage
            key={page}
            href={getPageURL(page)}
            current={page === currentPage}
            className={classNames}
          >
            {page}
          </PaginationPage>
        );
      }
    } else {
      pages.push(
        <PaginationPage key={currentPage} href={getPageURL(currentPage)} current>
          {currentPage}
        </PaginationPage>
      );

      if (currentPage > 1) {
        pages.unshift(
          <PaginationPage key={currentPage - 1} href={getPageURL(currentPage - 1)}>
            {currentPage - 1}
          </PaginationPage>
        );
      }

      if (currentPage > 2) {
        pages.unshift(
          <PaginationPage key={currentPage - 2} href={getPageURL(currentPage - 2)}>
            {currentPage - 2}
          </PaginationPage>
        );
        pages.push(<PaginationGap key="gap" />);
      }
    }

    return pages;
  };

  return (
    <Pagination className="flex flex-row justify-between bg-white w-full">
      <PaginationPrevious
        href={currentPage === 1 ? undefined : getPageURL(Math.max(1, currentPage - 1))}
      />
      <PaginationList className="w-2xl">{renderPageNumbers()}</PaginationList>
      <PaginationNext
        href={
          props.hasNextPage
            ? getPageURL(
                totalPages !== undefined ? Math.min(totalPages, currentPage + 1) : currentPage + 1
              )
            : undefined
        }
      />
    </Pagination>
  );
};
