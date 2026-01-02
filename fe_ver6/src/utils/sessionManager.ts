/**
 * Session management utilities
 */

import { SESSION_STORAGE_KEY } from './constants';

export const getSessionId = (): string | null => {
  try {
    return localStorage.getItem(SESSION_STORAGE_KEY);
  } catch (error) {
    console.error('Error getting session ID:', error);
    return null;
  }
};

export const saveSessionId = (sessionId: string): void => {
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  } catch (error) {
    console.error('Error saving session ID:', error);
  }
};

export const clearSessionId = (): void => {
  try {
    localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing session ID:', error);
  }
};
