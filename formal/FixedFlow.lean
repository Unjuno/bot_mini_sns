namespace MicroSNS

inductive State where
  | firstPost
  | readyForPost
deriving DecidableEq, Repr

inductive Input where
  | text (value : String)
  | image (mediaId : String)
  | audio (mediaId : String)
  | video (mediaId : String)
  | file (mediaId : String)
deriving Repr

inductive Action where
  | showUsage
  | saveText (value : String)
  | saveImage (mediaId : String)
  | saveAudio (mediaId : String)
  | saveVideo (mediaId : String)
  | saveFile (mediaId : String)
  | replyRecentPosts
deriving Repr

def step : State → Input → State × List Action
  | .firstPost, .text value =>
      (.readyForPost, [.saveText value, .showUsage])
  | .firstPost, .image mediaId =>
      (.readyForPost, [.saveImage mediaId, .showUsage])
  | .firstPost, .audio mediaId =>
      (.readyForPost, [.saveAudio mediaId, .showUsage])
  | .firstPost, .video mediaId =>
      (.readyForPost, [.saveVideo mediaId, .showUsage])
  | .firstPost, .file mediaId =>
      (.readyForPost, [.saveFile mediaId, .showUsage])
  | .readyForPost, .text value =>
      (.readyForPost, [.saveText value, .replyRecentPosts])
  | .readyForPost, .image mediaId =>
      (.readyForPost, [.saveImage mediaId, .replyRecentPosts])
  | .readyForPost, .audio mediaId =>
      (.readyForPost, [.saveAudio mediaId, .replyRecentPosts])
  | .readyForPost, .video mediaId =>
      (.readyForPost, [.saveVideo mediaId, .replyRecentPosts])
  | .readyForPost, .file mediaId =>
      (.readyForPost, [.saveFile mediaId, .replyRecentPosts])

def contains (action : Action) : List Action → Prop
  | [] => False
  | head :: tail => head = action ∨ contains action tail

def hasSave : List Action → Prop
  | [] => False
  | .saveText _ :: _ => True
  | .saveImage _ :: _ => True
  | .saveAudio _ :: _ => True
  | .saveVideo _ :: _ => True
  | .saveFile _ :: _ => True
  | _ :: tail => hasSave tail

def hasRecentReply : List Action → Prop
  | [] => False
  | .replyRecentPosts :: _ => True
  | _ :: tail => hasRecentReply tail

theorem first_text_is_saved_and_shows_usage (value : String) :
    hasSave (step .firstPost (.text value)).2 ∧
      contains .showUsage (step .firstPost (.text value)).2 := by
  simp [step, hasSave, contains]

theorem first_image_is_saved_and_shows_usage (mediaId : String) :
    hasSave (step .firstPost (.image mediaId)).2 ∧
      contains .showUsage (step .firstPost (.image mediaId)).2 := by
  simp [step, hasSave, contains]

theorem text_after_first_is_saved (value : String) :
    hasSave (step .readyForPost (.text value)).2 := by
  simp [step, hasSave]

theorem image_after_first_is_saved (mediaId : String) :
    hasSave (step .readyForPost (.image mediaId)).2 := by
  simp [step, hasSave]

theorem text_after_first_replies_recent_posts (value : String) :
    hasRecentReply (step .readyForPost (.text value)).2 := by
  simp [step, hasRecentReply]

theorem image_after_first_replies_recent_posts (mediaId : String) :
    hasRecentReply (step .readyForPost (.image mediaId)).2 := by
  simp [step, hasRecentReply]

end MicroSNS
