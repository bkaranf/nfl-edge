export type Market = 'moneyline' | 'spread' | 'total'
export type Mode = 'paper' | 'actual'
export interface Game {id:string; home:string; away:string; home_name:string; away_name:string; start_time:string; status:string; season_type:string}
export interface Pick {game_id:string; market:Market; side:'home'|'away'|'over'|'under'; line:number|null}
export interface Ref {book:string; source:string; kind:string; observed_at:string; age_seconds:number; eligible:boolean; probability:number; decimal_price:number|null; reason:string|null; adjacent_lines?:number[]}
export interface Row extends Pick {game:Game; references:Ref[]; probability:number|null; eligible_count:number; book_count:number; exchange_quotes:{ask:number; bid:number; observed_at:string; ticker:string}[]}
export interface Source {id:string; name:string; kind:string; url:string; note:string; status:string; last_success:string|null; attempted_at?:string; error?:string; quote_count:number; game_count:number; markets:string[]; skipped:number}
export interface Settings {bankroll:string; stake_pct:number; game_cap_pct:number; open_cap_pct:number; min_roi_pct:number; stress_pp:number; min_books:number; max_age_seconds:number; max_disagreement_pp:number; tie_max_pct:number}
export interface Sizing {configured:boolean; cap:number|null; game_open:number; total_open:number}
export interface Board {as_of:string; refreshing:boolean; sources:Source[]; settings:Settings; rows:Row[]; exposure:Record<Mode,Sizing>}
export interface Quote extends Pick {total_cost:string; winning_payout:string; observed_at:string; exchange:string; fees_confirmed:boolean; rules_confirmed:boolean; push_return:string|null; mode:Mode}
export interface Evaluation {id?:string; evaluated_at:string; qualified:boolean; label:string; reasons:string[]; assumptions:string; probability:{win:number|null; push:number|null; references:Ref[]; book_count:number; eligible_count:number; disagreement_pp:number|null; integer:boolean}; net:{ev:number; roi_pct:number; roi_high_pct:number; stress_roi_pct:number; max_cost:number; break_even_probability:number}|null; sizing:Sizing; within_cap:boolean; settings:Settings}
export interface Bet {id:string; created_at:string; quote:Quote; game:Game; evaluation:Evaluation; status:string; notes:string; settlement:{returned:string; result:string; pnl:number; at:string}|null; closing:{status:string; roi_pct?:number; reason?:string}|null}
