import { useState, useEffect } from "react";

export function useTypingEffect(fullText: string, speed = 50) {
  const [typedText, setTypedText] = useState("");

  useEffect(() => {
    if (fullText) {
      setTypedText("");
      let i = 0;
      const intervalId = setInterval(() => {
        setTypedText((prev) => prev + fullText.charAt(i));
        i++;
        if (i >= fullText.length) {
          clearInterval(intervalId);
        }
      }, speed);

      return () => {
        clearInterval(intervalId);
      };
    }
  }, [fullText, speed]);

  return typedText;
}
