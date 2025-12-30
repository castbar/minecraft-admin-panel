import { Injectable } from '@angular/core';
import { Preferences } from '@capacitor/preferences';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  private readonly PREFIX = 'minecraft_admin_';

  async set(key: string, value: any): Promise<void> {
    const prefixedKey = this.PREFIX + key;
    await Preferences.set({
      key: prefixedKey,
      value: typeof value === 'string' ? value : JSON.stringify(value)
    });
  }

  async get<T = any>(key: string): Promise<T | null> {
    const prefixedKey = this.PREFIX + key;
    const { value } = await Preferences.get({ key: prefixedKey });
    if (!value) return null;
    try {
      return JSON.parse(value) as T;
    } catch {
      return value as T;
    }
  }

  async remove(key: string): Promise<void> {
    const prefixedKey = this.PREFIX + key;
    await Preferences.remove({ key: prefixedKey });
  }

  async clear(): Promise<void> {
    const keys = await Preferences.keys();
    const prefixedKeys = keys.keys.filter(k => k.startsWith(this.PREFIX));
    for (const key of prefixedKeys) {
      await Preferences.remove({ key });
    }
  }
}

