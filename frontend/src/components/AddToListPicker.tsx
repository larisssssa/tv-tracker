import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ShowList } from "../types";

interface AddToListPickerProps {
  tvmazeShowId: number;
  onClose: () => void;
}

export function AddToListPicker({ tvmazeShowId, onClose }: AddToListPickerProps) {
  const [lists, setLists] = useState<ShowList[]>([]);
  const [memberOf, setMemberOf] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [newListName, setNewListName] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const allLists = await api.listLists();
      setLists(allLists);

      const details = await Promise.all(allLists.map((l) => api.getList(l.id)));
      const member = new Set(
        details
          .filter((d) => d.shows.some((s) => s.tvmaze_show_id === tvmazeShowId))
          .map((d) => d.id)
      );
      setMemberOf(member);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tvmazeShowId]);

  async function toggle(listId: number) {
    if (memberOf.has(listId)) {
      await api.removeShowFromList(listId, tvmazeShowId);
      setMemberOf((prev) => {
        const next = new Set(prev);
        next.delete(listId);
        return next;
      });
    } else {
      await api.addShowToList(listId, tvmazeShowId);
      setMemberOf((prev) => new Set(prev).add(listId));
    }
  }

  async function handleCreateAndAdd(e: FormEvent) {
    e.preventDefault();
    const name = newListName.trim();
    if (!name) return;

    setCreating(true);
    try {
      const newList = await api.createList(name);
      await api.addShowToList(newList.id, tvmazeShowId);
      setNewListName("");
      await load();
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="add-to-list-picker-backdrop" onClick={onClose}>
      <div className="add-to-list-picker" onClick={(e) => e.stopPropagation()}>
        <div className="add-to-list-picker-header">
          <h3>Add to list</h3>
          <button className="btn btn-ghost btn-small" onClick={onClose}>
            Close
          </button>
        </div>

        {loading ? (
          <p>Loading...</p>
        ) : (
          <ul className="add-to-list-picker-list">
            {lists.map((list) => (
              <li key={list.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={memberOf.has(list.id)}
                    onChange={() => toggle(list.id)}
                  />
                  {list.name}
                </label>
              </li>
            ))}
            {lists.length === 0 && <p>You don't have any lists yet.</p>}
          </ul>
        )}

        <form className="search-form" onSubmit={handleCreateAndAdd}>
          <input
            className="input"
            type="text"
            placeholder="Create new list..."
            value={newListName}
            onChange={(e) => setNewListName(e.target.value)}
          />
          <button className="btn btn-primary btn-small" type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create + add"}
          </button>
        </form>
      </div>
    </div>
  );
}
