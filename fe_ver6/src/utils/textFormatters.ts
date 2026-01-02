/**
 * Text formatting utilities
 */

/**
 * Remove <think> tags and their content from text
 */
export const removeThinkTags = (text: string): string => {
  return text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
};

/**
 * Format text content by preserving line breaks and basic formatting
 */
export const formatMessageContent = (text: string): string => {
  // Remove think tags first
  let cleaned = removeThinkTags(text);

  // Clean up excessive whitespace while preserving intentional line breaks
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  return cleaned;
};

/**
 * Parse simple markdown-like formatting to React elements
 * Supports: **bold**, line breaks, bullets
 */
export const parseFormattedText = (text: string): Array<{ type: string; content: string }> => {
  const cleaned = formatMessageContent(text);
  const lines = cleaned.split('\n');

  return lines.map((line, idx) => {
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      return { type: 'empty', content: '' };
    }

    // Bullet point
    if (trimmed.match(/^[-*•]\s/)) {
      return { type: 'bullet', content: trimmed.replace(/^[-*•]\s/, '') };
    }

    // Numbered list
    if (trimmed.match(/^\d+\.\s/)) {
      return { type: 'numbered', content: trimmed };
    }

    // Bold header (starts with **)
    if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
      return { type: 'header', content: trimmed.replace(/\*\*/g, '') };
    }

    // Regular paragraph
    return { type: 'paragraph', content: trimmed };
  });
};
