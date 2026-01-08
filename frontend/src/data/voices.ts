/** Voice data for Gemini Flash TTS */

export interface Voice {
  name: string;
  gender: 'female' | 'male';
}

export const VOICES: Voice[] = [
  // Female voices
  { name: 'Achernar', gender: 'female' },
  { name: 'Aoede', gender: 'female' },
  { name: 'Autonoe', gender: 'female' },
  { name: 'Callirrhoe', gender: 'female' },
  { name: 'Despina', gender: 'female' },
  { name: 'Erinome', gender: 'female' },
  { name: 'Gacrux', gender: 'female' },
  { name: 'Kore', gender: 'female' },
  { name: 'Laomedeia', gender: 'female' },
  { name: 'Leda', gender: 'female' },
  { name: 'Pulcherrima', gender: 'female' },
  { name: 'Sulafat', gender: 'female' },
  { name: 'Vindemiatrix', gender: 'female' },
  { name: 'Zephyr', gender: 'female' },
  
  // Male voices
  { name: 'Achird', gender: 'male' },
  { name: 'Algenib', gender: 'male' },
  { name: 'Algieba', gender: 'male' },
  { name: 'Alnilam', gender: 'male' },
  { name: 'Charon', gender: 'male' },
  { name: 'Enceladus', gender: 'male' },
  { name: 'Fenrir', gender: 'male' },
  { name: 'Iapetus', gender: 'male' },
  { name: 'Orus', gender: 'male' },
  { name: 'Puck', gender: 'male' },
  { name: 'Rasalgethi', gender: 'male' },
  { name: 'Sadachbia', gender: 'male' },
  { name: 'Sadaltager', gender: 'male' },
  { name: 'Schedar', gender: 'male' },
  { name: 'Umbriel', gender: 'male' },
  { name: 'Zubenelgenubi', gender: 'male' },
];

// Helper functions
export const getFemaleVoices = () => VOICES.filter(v => v.gender === 'female');
export const getMaleVoices = () => VOICES.filter(v => v.gender === 'male');
export const getVoiceByName = (name: string) => VOICES.find(v => v.name === name);

// Map voice names to actual audio file names (some have different spellings)
export const getAudioFileName = (voiceName: string): string => {
  const nameMap: Record<string, string> = {
    'Aoede': 'aoeda', // File is named aoeda, not aoede
  };
  
  const mappedName = nameMap[voiceName] || voiceName.toLowerCase();
  return `chirp3-hd-${mappedName}.wav`;
};
