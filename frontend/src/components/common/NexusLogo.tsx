import logoSrc from '../../assets/logo.jpg';

interface NexusLogoProps {
  size?: number;
  className?: string;
}

/**
 * Nexus brand mark — renders the project's logo.jpg asset.
 * The `size` prop sets both width and height so the image scales
 * uniformly at every call-site without layout changes.
 */
export default function NexusLogo({ size = 36, className = '' }: NexusLogoProps) {
  return (
    <img
      src={logoSrc}
      alt="Nexus logo"
      width={size}
      height={size}
      className={`object-contain ${className}`}
      style={{ width: size, height: size }}
    />
  );
}
