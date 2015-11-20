#ifndef _NOSUCH_LOOP_EVENT
#define _NOSUCH_LOOP_EVENT

#include <list>
#include "NosuchScheduler.h"

#define DEFAULT_LOOPFADE 0.7f
#define MIN_LOOP_VELOCITY 5

class SchedEvent;

typedef std::list<SchedEvent*> SchedEventList;

class PaletteHost;
class Region;

class NosuchLoop {
public:
	NosuchLoop(PaletteHost* mf, int id, Region* r) {
		_paletteHost = mf;
		_click = 0;
		_region = r;
		_id = id;
		NosuchLockInit(&_loop_mutex,"loop");
	};
	~NosuchLoop() {
		NosuchDebug(1,"NosuchLoop DESTRUCTOR!");
	}
	void Clear();
	void AdvanceClickBy1();
	int AddLoopEvent(SchedEvent* e);
	std::string DebugString(std::string indent = "");
	void SendMidiLoopOutput(MidiMsg* mm);
	int id() { return _id; }
	click_t click() { return _click; }
	int NumNotes();
	void NumEvents(int& nnotes, int& ncontrollers);
	void removeOldestNoteOn();
	Region* region() { NosuchAssert(_region); return _region; }

private:
	SchedEventList _events;
	click_t _click; // relative within loop
	int _id;
	PaletteHost* _paletteHost;
	Region* _region;

	pthread_mutex_t _loop_mutex;
	void Lock() { NosuchLock(&_loop_mutex,"loop"); }
	void Unlock() { NosuchUnlock(&_loop_mutex,"loop"); }

	SchedEventIterator findNoteOff(MidiNoteOn* noteon, SchedEventIterator& it);
	SchedEventIterator oldestNoteOn();
	void removeNote(SchedEventIterator it);
	void ClearNoLock();
};

class NosuchLooper : public NosuchClickClient {
public:
	NosuchLooper(PaletteHost* b);
	~NosuchLooper();
	void AdvanceClickTo(int click, NosuchScheduler* s);
	std::string DebugString();
	void AddLoop(NosuchLoop* loop);

private:
	std::vector<NosuchLoop*> _loops;
	int _last_click;
	PaletteHost* _paletteHost;
	pthread_mutex_t _looper_mutex;

	void Lock() { NosuchLock(&_looper_mutex,"looper"); }
	void Unlock() { NosuchUnlock(&_looper_mutex,"looper"); }

};

#endif