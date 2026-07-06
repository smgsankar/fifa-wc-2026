export interface Team {
  id: number
  name: string
  country_code: string
  logo_url: string | null
  /** Undecided knockout slot (e.g. "Winner SF 1") standing in for a real team. */
  is_placeholder?: boolean
}

export interface SquadPlayer {
  player_id: number
  name: string
  position: string
  number: number
}

export type FormResult = 'W' | 'D' | 'L'

export interface FormEntry {
  match_date: string
  opponent: string
  result: FormResult
  score: string
}

export interface TeamDetail extends Team {
  head_coach: string | null
  squad: SquadPlayer[]
  recent_form: FormEntry[]
}

export interface Prediction {
  team_a_win_prob: number
  team_b_win_prob: number
  draw_prob: number
  confidence: number
}

export interface LastMatch {
  date: string
  result: string | null
  score: string | null
}

export interface H2H {
  team_a_wins: number
  team_b_wins: number
  draws: number
  last_match: LastMatch | null
}

export type MatchStatus = 'pending' | 'live' | 'awaiting_results' | 'completed'

export interface MatchSummary {
  match_id: number
  team_a: Team
  team_b: Team
  match_date: string
  stadium: string | null
  city: string | null
  stage: string
  status: MatchStatus
  prediction: Prediction | null
}

/** How a completed match was decided; null when unknown (pre-existing data). */
export type DecidedBy = 'regular' | 'extra_time' | 'penalties'

export interface MatchListItem extends MatchSummary {
  actual_score_a: number | null
  actual_score_b: number | null
  /** actual_score_* includes extra time; a shootout's score is penalty_score_*. */
  decided_by: DecidedBy | null
  penalty_score_a: number | null
  penalty_score_b: number | null
  prediction_correct: boolean | null
}

export interface MatchDetail extends Omit<MatchListItem, 'team_a' | 'team_b'> {
  team_a: TeamDetail
  team_b: TeamDetail
  h2h: H2H | null
}

export interface ModelStats {
  total_predictions: number
  correct_predictions: number
  incorrect_predictions: number
  accuracy: number
  precision: number
  recall: number
  last_updated: string
}
