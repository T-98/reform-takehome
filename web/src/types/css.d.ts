// Type declarations for CSS module imports
declare module "*.css" {
  const content: { [className: string]: string };
  export default content;
}

// Specific declarations for react-pdf CSS files
declare module "react-pdf/dist/Page/TextLayer.css";
declare module "react-pdf/dist/Page/AnnotationLayer.css";
