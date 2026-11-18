import { ArrowRight } from '@phosphor-icons/react/dist/csr/ArrowRight'
import { ArrowSquareOut } from '@phosphor-icons/react/dist/csr/ArrowSquareOut'
import { Book } from '@phosphor-icons/react/dist/csr/Book'
import { BookOpen } from '@phosphor-icons/react/dist/csr/BookOpen'
import { BracketsCurly } from '@phosphor-icons/react/dist/csr/BracketsCurly'
import { ChatCircle } from '@phosphor-icons/react/dist/csr/ChatCircle'
import { Check } from '@phosphor-icons/react/dist/csr/Check'
import { ClockCounterClockwise } from '@phosphor-icons/react/dist/csr/ClockCounterClockwise'
import { Command } from '@phosphor-icons/react/dist/csr/Command'
import { Copy } from '@phosphor-icons/react/dist/csr/Copy'
import { Database } from '@phosphor-icons/react/dist/csr/Database'
import { GearSix } from '@phosphor-icons/react/dist/csr/GearSix'
import { GlobeHemisphereWest } from '@phosphor-icons/react/dist/csr/GlobeHemisphereWest'
import { Info } from '@phosphor-icons/react/dist/csr/Info'
import { Key } from '@phosphor-icons/react/dist/csr/Key'
import { Lightning } from '@phosphor-icons/react/dist/csr/Lightning'
import { List } from '@phosphor-icons/react/dist/csr/List'
import { MagnifyingGlass } from '@phosphor-icons/react/dist/csr/MagnifyingGlass'
import { Moon } from '@phosphor-icons/react/dist/csr/Moon'
import { Pulse } from '@phosphor-icons/react/dist/csr/Pulse'
import { ShieldCheck } from '@phosphor-icons/react/dist/csr/ShieldCheck'
import { Sparkle } from '@phosphor-icons/react/dist/csr/Sparkle'
import { Stack } from '@phosphor-icons/react/dist/csr/Stack'
import { Sun } from '@phosphor-icons/react/dist/csr/Sun'
import { TerminalWindow } from '@phosphor-icons/react/dist/csr/TerminalWindow'
import { Trash } from '@phosphor-icons/react/dist/csr/Trash'
import { XCircle } from '@phosphor-icons/react/dist/csr/XCircle'

// One icon family, one weight, everywhere.
const registry = {
  search: MagnifyingGlass,
  settings: GearSix,
  code: BracketsCurly,
  sparkles: Sparkle,
  copy: Copy,
  check: Check,
  external: ArrowSquareOut,
  sun: Sun,
  moon: Moon,
  close: XCircle,
  arrow: ArrowRight,
  history: ClockCounterClockwise,
  trash: Trash,
  key: Key,
  shield: ShieldCheck,
  database: Database,
  book: Book,
  bolt: Lightning,
  globe: GlobeHemisphereWest,
  bookOpen: BookOpen,
  message: ChatCircle,
  refresh: ClockCounterClockwise,
  menu: List,
  info: Info,
  terminal: TerminalWindow,
  stack: Stack,
  command: Command,
  pulse: Pulse,
}

export function Icon({ name, size = 18, className = '', ...rest }) {
  const Glyph = registry[name] || Info
  return <Glyph size={size} weight="regular" className={className} aria-hidden="true" {...rest} />
}
