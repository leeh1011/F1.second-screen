import type { Tyre } from "@/types";

const LETTER = { SOFT: "S", MEDIUM: "M", HARD: "H" } as const;
const LABEL = { SOFT: "소프트", MEDIUM: "미디엄", HARD: "하드" } as const;

// 타이어 옆면 표시처럼 컴파운드 색 링 + 글자, 옆에 사용한 랩 수
function TyreMark({ tyre }: { tyre: Tyre }) {
  return (
    <span className="tyre">
      <span className={`tyre-ring tyre-${tyre.compound.toLowerCase()}`} aria-hidden="true">
        {LETTER[tyre.compound]}
      </span>
      <span className="sr-only">{LABEL[tyre.compound]} 타이어</span>
      <span className="tyre-age">{tyre.age}랩</span>
    </span>
  );
}

export default TyreMark;
