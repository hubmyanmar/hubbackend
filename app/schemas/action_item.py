from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, constr


class ActionItemStatus(str, Enum):
    to_do = "to_do"
    in_progress = "in_progress"
    complete = "complete"


class ActionItemBase(BaseModel):
    task: constr(max_length=255)
    owner_name: constr(max_length=255)
    due_date: Optional[date] = None
    status: ActionItemStatus = ActionItemStatus.to_do


class ActionItemCreate(ActionItemBase):
    meeting_id: int

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ActionModal from '../components/Records/ActionModal';
import LeftPanel from '../components/Records/LeftPanel';
import MeetingHeader from '../components/Records/MeetingHeader';
import RightPanel from '../components/Records/RightPanel';
import StatusBanner from '../components/Records/StatusBanner';

import { useRecording } from '../context/RecordingContext';

// 🕒 Helper Function
const formatTimeToAMPM = (timeStr) => {
  if (!timeStr) return '';
  const str = String(timeStr).trim();
  
  if (str.toUpperCase().includes('AM') || str.toUpperCase().includes('PM')) {
    return str.toUpperCase();
  }
  
  const parts = str.split(':');
  if (parts.length < 2) return str;

  let hours = parseInt(parts[0], 10);
  const minutes = parts[1];

  if (isNaN(hours)) return str;

  const modifier = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12;

  return `${String(hours).padStart(2, '0')}:${minutes} ${modifier}`;
};

export default function LiveMeeting({ 
  selectedMeetingData: propMeetingData, 
  currentUser, 
  refreshSessions, 
  onSaveSession 
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);

  // 👤 User Data ကို Props မှသာ တိုက်ရိုက်ယူပါမည် (Storage လုံးဝ မသုံးပါ)
  const activeUser = currentUser || {};
  const userId = activeUser?.id || activeUser?._id || 'guest_user';

  const { 
    status, actionType, timer, fileName, liveTranscript, 
    handleStart, handleFileUpload, handlePause, handleResume, handleStop, formatTime 
  } = useRecording();

  // State Management (Navigation State သို့မဟုတ် Props မှသာ Data ရယူမည်)
  const [selectedMeetingData, setSelectedMeetingData] = useState(() => {
    return propMeetingData || location.state || null;
  });

  useEffect(() => {
    const passedData = propMeetingData || location.state;
    if (passedData) {
      setSelectedMeetingData(passedData);
    }
  }, [propMeetingData, location.state]);

  const rawMeeting = selectedMeetingData?.meeting || selectedMeetingData || {};

  const mockSummary = {
    englishSummary: "This is a test English summary for the meeting discussion.",
    myanmarSummary: "ဒါကတော့ အစည်းအဝေးအတွက် စမ်းသပ်ရေးသားထားတဲ့ မြန်မာလို အကျဉ်းချုပ် ဖြစ်ပါတယ်။",
    keyDecisions: [
      "Decision 1: Approved budget",
      "Decision 2: Next meeting on Friday"
    ],
    actionItems: [
      {
        task: "Prepare report",
        owner: "Aung Aung",
        dueDate: "2026-09-12",
        status: "To Do",
        priority: "High"
      },
      {
        task: "Update budget",
        owner: "Su Su",
        dueDate: "2026-09-13",
        status: "In Progress",
        priority: "Low"
      }
    ],
  };

  const formattedStartTime = formatTimeToAMPM(rawMeeting.startTime || rawMeeting.start_time || rawMeeting.time);

  const meeting = { 
    ...rawMeeting, 
    startTime: formattedStartTime,
    ...mockSummary
  };

  const [showModal, setShowModal] = useState(false); 

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  // 🚀 Join နှိပ်ပြီး ဝင်လာပါက Modal မပြဘဲ Recording တန်းစတင်ပေးမည့် Logic
  useEffect(() => {
    const isAutoStart = location.state?.autoStart || selectedMeetingData?.autoStart;
    const isJoinMode = location.state?.mode === 'join' || selectedMeetingData?.mode === 'join';

    if (isAutoStart && isJoinMode && status === 'idle') {
      setShowModal(false);
      handleStart('mic'); // Auto Microphone start
    } else if (status !== 'idle') {
      setShowModal(false);
    } else {
      if (selectedMeetingData?.mode === 'view' || meeting?.status === 'stopped') {
        setShowModal(false);
      } else {
        setShowModal(true);
      }
    }
  }, [status, selectedMeetingData, meeting?.status, location.state]);

  const onStartRecording = (type) => {
    setShowModal(false);
    handleStart(type);
  };

  const onUpload = (e) => {
    setShowModal(false);
    handleFileUpload(e);
  };

  // 🛑 Stop နှိပ်ပါက App.jsx ထဲက onSaveSession (သို့မဟုတ် refreshSessions) ကို တိုက်ရိုက် ခေါ်သုံးမည်
  const onStopRecording = async () => {
    try {
      const meetingId = meeting.id || rawMeeting.id || `meeting-${Date.now()}`;

      const sessionPayload = {
        meeting_id: meetingId,
        user_id: userId,
        title: meeting.title || "Untitled Meeting",
        date: meeting.date || new Date().toISOString().split('T')[0],
        status: 'stopped',
        stopped_at: new Date().toISOString(),
        english_summary: meeting.englishSummary || '',
        myanmar_summary: meeting.myanmarSummary || '',
        key_decisions: meeting.keyDecisions || [],
        action_items: meeting.actionItems || []
      };

      // 🌐 1. App.jsx မှ ရရှိသော Save function ဖြင့် Database ထို့ သို့ ပို့မည်
      if (onSaveSession) {
        await onSaveSession(sessionPayload);
      } else if (refreshSessions) {
        await refreshSessions();
      }

      // 2. State ကို Local တွင် View mode သို့ အလိုအလျောက် ပြောင်းလဲပေးမည်
      setSelectedMeetingData(prev => ({
        ...prev,
        meeting: { ...prev?.meeting, status: 'stopped' },
        mode: 'view'
      }));

      // 3. Recording ရပ်မည်
      if (handleStop) {
        handleStop();
      }

    } catch (error) {
      console.error("Error during stop recording:", error);
    }
  };

  return (
    <div className="relative flex flex-col gap-6 max-w-[1400px] mx-auto w-full pb-10">
      {showModal && (
        <button 
          onClick={handleGoHome}
          className="absolute top-0 right-0 z-50 p-2 text-gray-500 hover:text-red-500 hover:bg-gray-100 rounded-full transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      <ActionModal 
        showModal={showModal} 
        handleStart={onStartRecording} 
        fileInputRef={fileInputRef} 
        handleFileUpload={onUpload}
        onClose={handleGoHome} 
      />

      <MeetingHeader 
        title={meeting?.title || "Untitled Meeting"} 
        date={meeting?.date}
        startTime={meeting?.startTime}
        endTime={meeting?.endTime}
        room={meeting?.room || meeting?.location}
        participants={meeting?.participants}
        englishSummary={meeting?.englishSummary}
        myanmarSummary={meeting?.myanmarSummary}
        keyDecisions={meeting?.keyDecisions}
        actionItems={meeting?.actionItems}
      />

      <StatusBanner 
        status={status} 
        actionType={actionType} 
        timer={timer} 
        fileName={fileName} 
        formatTime={formatTime} 
        handleStop={onStopRecording}
        handlePause={handlePause}
        handleResume={handleResume}
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-6 mt-2 items-start">
        <LeftPanel 
          status={status}
          timer={timer} 
          formatTime={formatTime}
          handlePause={handlePause} 
          handleResume={handleResume} 
          englishSummary={meeting.englishSummary}
          myanmarSummary={meeting.myanmarSummary}
        />
        <RightPanel 
          status={status} 
          actionType={actionType}
          liveTranscript={liveTranscript}
          keyDecisions={meeting.keyDecisions}
          actionItems={meeting.actionItems}
        />
      </div>
    </div>
  );
}
class ActionItemUpdate(BaseModel):
    task: Optional[constr(max_length=255)] = None
    owner_name: Optional[constr(max_length=255)] = None
    due_date: Optional[date] = None
    status: Optional[ActionItemStatus] = None


class ActionItemOut(ActionItemBase):
    id: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
