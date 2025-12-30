import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface PlayersOnlineResponse {
  players: string[];
  player_count: number;
  max_players: number;
}

@Injectable({
  providedIn: 'root'
})
export class PlayersOnlineService {
  constructor(private api: ApiService) {}

  getPlayersOnline(serverId: number): Observable<PlayersOnlineResponse> {
    return this.api.get<PlayersOnlineResponse>(`/servers/${serverId}/players/online/`);
  }
}

