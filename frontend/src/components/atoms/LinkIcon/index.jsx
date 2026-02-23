import Proptypes from "prop-types";
const LinkIcon = (props) => {
  const { link, target, src, altText, height, width } = props;

  return (
    <>
      <a target={target} href={link} rel="noopener noreferrer">
        {src ? (
          <img
            src={src}
            alt={altText}
            style={{ height: height, width: width }}
          />
        ) : (
          altText
        )}
      </a>
    </>
  );
};
LinkIcon.propTypes = {
  link: Proptypes.string,
  target: Proptypes.string,
  src: Proptypes.node,
  altText: Proptypes.string,
  height: Proptypes.number,
  width: Proptypes.number,
};
export default LinkIcon;
