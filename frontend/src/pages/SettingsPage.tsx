import { useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useSettingsStore } from '../store/useSettingsStore';
import { VOICES, Voice, getAudioFileName } from '../data/voices';
import './SettingsPage.css';

function SettingsPage() {
  const navigate = useNavigate();
  const { selectedVoice, setVoice } = useSettingsStore();
  const [tempVoice, setTempVoice] = useState(selectedVoice);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Cleanup: Stop audio when component unmounts or user navigates away
  useEffect(() => {
    return () => {
      // Stop audio playback when component unmounts
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current = null;
      }
      setIsPlaying(false);
      setPlayingVoice(null);
    };
  }, []);

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsPlaying(false);
    setPlayingVoice(null);
  };

  const handleVoiceSelect = (voiceName: string) => {
    setTempVoice(voiceName);
  };

  const handlePreview = async (voiceName: string) => {
    // Stop current audio if playing
    stopAudio();

    // If clicking the same voice that's playing, stop it
    if (playingVoice === voiceName && isPlaying) {
      return;
    }

    setIsPlaying(true);
    setPlayingVoice(voiceName);

    try {
      // Use helper function to get correct audio file name
      const audioFileName = getAudioFileName(voiceName);
      const audioPath = `/voice/${audioFileName}`;
      console.log('Attempting to play:', audioPath);
      const audio = new Audio(audioPath);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        setPlayingVoice(null);
        audioRef.current = null;
      };

      audio.onerror = (e) => {
        setIsPlaying(false);
        setPlayingVoice(null);
        audioRef.current = null;
        console.error(`Failed to load audio for ${voiceName}:`, audioPath, e);
        alert(`無法載入音色試聽檔案：${voiceName}\n檔案路徑：${audioPath}`);
      };

      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsPlaying(false);
      setPlayingVoice(null);
      audioRef.current = null;
      alert(`播放失敗：${error}`);
    }
  };

  const handleSave = () => {
    // Stop audio before navigating away
    stopAudio();
    setVoice(tempVoice);
    navigate(-1); // Go back to previous page
  };

  const handleCancel = () => {
    // Stop audio before navigating away
    stopAudio();
    navigate(-1);
  };

  const femaleVoices = VOICES.filter(v => v.gender === 'female');
  const maleVoices = VOICES.filter(v => v.gender === 'male');

  return (
    <div className="settings-page">
      <div className="settings-container">
        {/* Header */}
        <div className="settings-header">
          <button 
            className="back-button glass"
            onClick={handleCancel}
            aria-label="返回"
          >
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <div className="header-content">
            <h1 className="page-title">音色設定</h1>
            <p className="page-description">選擇您喜歡的 AI 解說音色</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="settings-content">
          {/* Female Voices Section */}
          <section className="voice-section">
            <div className="section-header">
              <svg className="section-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <h2 className="section-title">女性音色</h2>
              <span className="voice-count">{femaleVoices.length} 個音色</span>
            </div>
            
            <div className="voice-grid">
              {femaleVoices.map((voice) => (
                <VoiceCard
                  key={voice.name}
                  voice={voice}
                  isSelected={tempVoice === voice.name}
                  isPlaying={isPlaying && playingVoice === voice.name}
                  onSelect={() => handleVoiceSelect(voice.name)}
                  onPreview={() => handlePreview(voice.name)}
                />
              ))}
            </div>
          </section>

          {/* Male Voices Section */}
          <section className="voice-section">
            <div className="section-header">
              <svg className="section-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <h2 className="section-title">男性音色</h2>
              <span className="voice-count">{maleVoices.length} 個音色</span>
            </div>
            
            <div className="voice-grid">
              {maleVoices.map((voice) => (
                <VoiceCard
                  key={voice.name}
                  voice={voice}
                  isSelected={tempVoice === voice.name}
                  isPlaying={isPlaying && playingVoice === voice.name}
                  onSelect={() => handleVoiceSelect(voice.name)}
                  onPreview={() => handlePreview(voice.name)}
                />
              ))}
            </div>
          </section>
        </div>

        {/* Action Buttons */}
        <div className="settings-actions">
          <button className="action-button secondary" onClick={handleCancel}>
            取消
          </button>
          <button className="action-button primary" onClick={handleSave}>
            <svg className="button-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>儲存設定</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// Voice Card Component
interface VoiceCardProps {
  voice: Voice;
  isSelected: boolean;
  isPlaying: boolean;
  onSelect: () => void;
  onPreview: () => void;
}

function VoiceCard({ voice, isSelected, isPlaying, onSelect, onPreview }: VoiceCardProps) {
  return (
    <div 
      className={`voice-card glass ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <div className="voice-card-content">
        <div className="voice-name">{voice.name}</div>
        
        <button
          className={`preview-button ${isPlaying ? 'playing' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onPreview();
          }}
          aria-label={isPlaying ? '停止試聽' : '試聽'}
        >
          {isPlaying ? (
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </button>
      </div>
      
      {isSelected && (
        <div className="selected-indicator">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}
    </div>
  );
}

export default SettingsPage;
