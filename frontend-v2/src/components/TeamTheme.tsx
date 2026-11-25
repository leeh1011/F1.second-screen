"use client";

import { useEffect } from "react";
import { themeFor } from "@/lib/teams";

// 화면 전체의 강조색을 팀 색으로 바꾼다. (globals.css의 --accent 는 색 전환 애니메이션이 걸려 있다)
// team 이 바뀌면(선두 교체 등) 색이 천천히 넘어가고, 화면을 떠나면 중립색으로 돌아간다.
function TeamTheme({ team }: { team?: string | null }) {
  useEffect(() => {
    const t = themeFor(team);
    const root = document.documentElement;
    root.style.setProperty("--accent", t.accent);
    root.style.setProperty("--on-accent", t.on);
    return () => {
      root.style.removeProperty("--accent");
      root.style.removeProperty("--on-accent");
    };
  }, [team]);

  return null;
}

export default TeamTheme;
