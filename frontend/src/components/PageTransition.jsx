import { useLocation, useOutlet } from "react-router-dom";
import { cloneElement, useRef, useEffect, useState } from "react";

/**
 * Wraps each route's outlet in a fade-slide page transition.
 * On route change: old page fades out, new page fades in (250ms).
 */
export default function PageTransition({ children }) {
  const location = useLocation();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [transitionStage, setTransitionStage] = useState("enter");
  const prevPathRef = useRef(location.pathname);

  useEffect(() => {
    if (location.pathname !== prevPathRef.current) {
      setTransitionStage("exit");
      const timeout = setTimeout(() => {
        setDisplayChildren(children);
        setTransitionStage("enter");
        prevPathRef.current = location.pathname;
      }, 200);
      return () => clearTimeout(timeout);
    } else {
      setDisplayChildren(children);
      setTransitionStage("enter");
      prevPathRef.current = location.pathname;
    }
  }, [children, location.pathname]);

  return (
    <div
      className={
        transitionStage === "enter"
          ? "page-transition-enter"
          : "opacity-0 translate-y-2"
      }
      style={{
        transition: "opacity 0.2s var(--ease-out), transform 0.2s var(--ease-out)",
      }}
    >
      {displayChildren}
    </div>
  );
}