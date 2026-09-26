import { Link } from 'react-router-dom';
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** When set, renders a router Link with identical styling instead of a <button>. */
  to?: string;
  children: ReactNode;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'nx-btn-primary',
  secondary: 'nx-btn-secondary',
  ghost: 'nx-btn-ghost',
};

const sizeOverrides: Record<ButtonSize, string> = {
  sm: 'px-4 py-2 text-xs',
  md: '',           // default size already baked into nx-btn-* classes
  lg: 'px-6 py-3 text-base',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  to,
  children,
  className = '',
  type = 'button',
  ...rest
}: ButtonProps) {
  const classes = [
    variantClasses[variant],
    sizeOverrides[size],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  if (to !== undefined) {
    const linkProps = rest as AnchorHTMLAttributes<HTMLAnchorElement>;
    return (
      <Link to={to} className={classes} onClick={linkProps.onClick}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} className={classes} {...rest}>
      {children}
    </button>
  );
}
