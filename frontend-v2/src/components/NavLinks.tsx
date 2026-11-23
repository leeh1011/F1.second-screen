"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "홈" },
  { href: "/drivers", label: "드라이버" },
  { href: "/live", label: "라이브" },
];

function NavLinks() {
  const pathname = usePathname();

  return (
    <nav className="nav" aria-label="주 메뉴">
      {links.map((l) => {
        const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            className="nav-link"
            aria-current={active ? "page" : undefined}
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}

export default NavLinks;
