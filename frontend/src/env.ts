/** True for the static GitHub Pages build, which has no server behind it. */
export const STATIC_DEMO = import.meta.env.MODE === "pages";
export const BASE = import.meta.env.BASE_URL;
export const REPO_URL = "https://github.com/Hafsa-Anwar65/Bill-Sight";
export const DEMO_MESSAGE =
  "This online demo has no server, so it can't read new bills or answer chat questions. Open a sample bill, or run Billsight on your computer to analyse your own.";
