import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ShowList, ShowListDetail } from "../types";

export function ListsPage() {
  const [lists, setLists] = useState<ShowList[]>([]);
  const [loading, setLoading] = useState(true);
  const [newListName, setNewListName] = useState("");
  const [creating, setCreating] = useState(false);
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [selectedList, setSelectedList] = useState<ShowListDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  async function refreshLists() {
    setLoading(true);
    try {
      setLists(await api.listLists());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshLists();
  }, []);

  async function openList(listId: number) {
    setDetailLoading(true);
    try {
      setSelectedList(await api.getList(listId));
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    const name = newListName.trim();
    if (!name) return;

    setCreating(true);
    try {
      await api.createList(name);
      setNewListName("");
      await refreshLists();
    } finally {
      setCreating(false);
    }
  }

  function startRename(list: ShowList) {
    setRenamingId(list.id);
    setRenameValue(list.name);
  }

  async function handleRename(listId: number) {
    const name = renameValue.trim();
    if (!name) return;
    await api.renameList(listId, name);
    setRenamingId(null);
    await refreshLists();
    if (selectedList?.id === listId) await openList(listId);
  }

  async function handleDelete(listId: number) {
    const confirmed = window.confirm(
      "Delete this list? The shows in it will not be removed from My Shows."
    );
    if (!confirmed) return;
    await api.deleteList(listId);
    if (selectedList?.id === listId) setSelectedList(null);
    await refreshLists();
  }

  async function handleRemoveShow(tvmazeShowId: number) {
    if (!selectedList) return;
    await api.removeShowFromList(selectedList.id, tvmazeShowId);
    await openList(selectedList.id);
  }

  async function handleAddToMyShows(tvmazeShowId: number) {
    await api.trackShow(tvmazeShowId);
  }

  if (selectedList) {
    return (
      <div className="lists-page">
        <div className="page-header">
          <button className="btn btn-ghost btn-small" onClick={() => setSelectedList(null)}>
            &larr; All lists
          </button>
          <h2 className="page-title">{selectedList.name}</h2>
          <p className="page-subtitle">
            {selectedList.shows.length} show{selectedList.shows.length === 1 ? "" : "s"}
          </p>
        </div>

        {detailLoading ? (
          <p>Loading...</p>
        ) : selectedList.shows.length === 0 ? (
          <div className="empty-state">
            <p>This list is empty.</p>
            <Link to="/search" className="btn btn-primary">
              Search for a show to add
            </Link>
          </div>
        ) : (
          <ul className="show-list">
            {selectedList.shows.map((show) => (
              <li key={show.tvmaze_show_id} className="show-list-item">
                {show.image && <img src={show.image} alt={show.name} />}
                <div className="show-info">
                  <div className="show-title-row">
                    <Link className="show-name" to={`/shows/${show.tvmaze_show_id}`}>
                      {show.name}
                    </Link>
                    {show.status && (
                      <span className={`status-badge status-${show.status.toLowerCase()}`}>
                        {show.status}
                      </span>
                    )}
                  </div>
                </div>
                <div className="actions">
                  <button
                    className="btn btn-primary btn-small"
                    onClick={() => handleAddToMyShows(show.tvmaze_show_id)}
                  >
                    Add to My Shows
                  </button>
                  <button
                    className="btn btn-ghost btn-small"
                    onClick={() => handleRemoveShow(show.tvmaze_show_id)}
                  >
                    Remove from list
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  return (
    <div className="lists-page">
      <div className="page-header">
        <h2 className="page-title">Lists</h2>
        <p className="page-subtitle">
          Organize tracked and untracked shows into custom lists.
        </p>
      </div>

      <form className="search-form" onSubmit={handleCreate}>
        <input
          className="input"
          type="text"
          placeholder="New list name..."
          value={newListName}
          onChange={(e) => setNewListName(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={creating}>
          {creating ? "Creating..." : "Create list"}
        </button>
      </form>

      {loading ? (
        <p>Loading...</p>
      ) : lists.length === 0 ? (
        <div className="empty-state">
          <p>You haven't created any lists yet.</p>
        </div>
      ) : (
        <ul className="show-list">
          {lists.map((list) => (
            <li key={list.id} className="show-list-item">
              <div className="show-info">
                {renamingId === list.id ? (
                  <form
                    className="search-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleRename(list.id);
                    }}
                  >
                    <input
                      className="input"
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      autoFocus
                    />
                    <button className="btn btn-primary btn-small" type="submit">
                      Save
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost btn-small"
                      onClick={() => setRenamingId(null)}
                    >
                      Cancel
                    </button>
                  </form>
                ) : (
                  <button className="show-name link-button" onClick={() => openList(list.id)}>
                    {list.name}
                  </button>
                )}
              </div>
              {renamingId !== list.id && (
                <div className="actions">
                  <button
                    className="btn btn-primary btn-small"
                    onClick={() => openList(list.id)}
                  >
                    View
                  </button>
                  <button
                    className="btn btn-ghost btn-small"
                    onClick={() => startRename(list)}
                  >
                    Rename
                  </button>
                  <button
                    className="btn btn-ghost btn-small"
                    onClick={() => handleDelete(list.id)}
                  >
                    Delete
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
