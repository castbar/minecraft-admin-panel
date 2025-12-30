import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface ModTemplate {
  id: number;
  mod_name: string;
  config_file_path: string;
  default_content: string;
  file_format: 'json' | 'yaml' | 'properties' | 'toml' | 'txt';
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateModTemplateRequest {
  mod_name: string;
  config_file_path: string;
  default_content: string;
  file_format: 'json' | 'yaml' | 'properties' | 'toml' | 'txt';
  description?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ModTemplateService {
  constructor(private api: ApiService) {}

  getTemplates(): Observable<ModTemplate[]> {
    return this.api.get<ModTemplate[]>('/mods/templates/');
  }

  getTemplate(templateId: number): Observable<ModTemplate> {
    return this.api.get<ModTemplate>(`/mods/templates/${templateId}/`);
  }

  createTemplate(data: CreateModTemplateRequest): Observable<ModTemplate> {
    return this.api.post<ModTemplate>('/mods/templates/create/', data);
  }

  updateTemplate(templateId: number, data: Partial<CreateModTemplateRequest>): Observable<ModTemplate> {
    return this.api.put<ModTemplate>(`/mods/templates/${templateId}/update/`, data);
  }
}

