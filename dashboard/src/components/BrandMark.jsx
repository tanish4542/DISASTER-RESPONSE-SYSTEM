import { PRODUCT_NAME } from '../brand';

const LOGO_SRC = '/resqnet-logo.png';

export default function BrandMark({ compact = false }) {
  return (
    <span className={`brand-mark ${compact ? 'compact' : ''}`}>
      <img
        className="brand-mark-logo"
        src={LOGO_SRC}
        alt={PRODUCT_NAME}
        width="1254"
        height="1254"
      />
    </span>
  );
}
