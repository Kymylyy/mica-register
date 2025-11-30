import { useState } from 'react';
import api from '../utils/api';

export function TagManager({ entityId, tags, onTagsUpdate }) {
  const [newTagName, setNewTagName] = useState('');
  const [newTagValue, setNewTagValue] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddTag = async () => {
    if (!newTagName.trim()) return;

    try {
      await api.post(`/api/entities/${entityId}/tags`, {
        tag_name: newTagName.trim(),
        tag_value: newTagValue.trim() || null,
      });
      setNewTagName('');
      setNewTagValue('');
      setIsAdding(false);
      onTagsUpdate();
    } catch (error) {
      console.error('Error adding tag:', error);
      alert(error.response?.data?.detail || 'Failed to add tag');
    }
  };

  const handleRemoveTag = async (tagName) => {
    try {
      await api.delete(`/api/entities/${entityId}/tags/${tagName}`);
      onTagsUpdate();
    } catch (error) {
      console.error('Error removing tag:', error);
      alert('Failed to remove tag');
    }
  };

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-700">Tags</h3>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-xs text-primary hover:underline"
          >
            + Add tag
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-2 p-2 bg-gray-50 rounded">
          <input
            type="text"
            placeholder="Tag name"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            className="w-full mb-2 px-2 py-1 text-sm border border-gray-300 rounded"
          />
          <input
            type="text"
            placeholder="Tag value (optional)"
            value={newTagValue}
            onChange={(e) => setNewTagValue(e.target.value)}
            className="w-full mb-2 px-2 py-1 text-sm border border-gray-300 rounded"
          />
          <div className="flex gap-2">
            <button
              onClick={handleAddTag}
              className="px-3 py-1 text-xs bg-primary text-white rounded hover:bg-blue-600"
            >
              Add
            </button>
            <button
              onClick={() => {
                setIsAdding(false);
                setNewTagName('');
                setNewTagValue('');
              }}
              className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {tags.map(tag => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded"
          >
            {tag.tag_name}
            {tag.tag_value && <span className="text-purple-600">: {tag.tag_value}</span>}
            <button
              onClick={() => handleRemoveTag(tag.tag_name)}
              className="ml-1 text-purple-600 hover:text-purple-800"
            >
              ×
            </button>
          </span>
        ))}
        {tags.length === 0 && !isAdding && (
          <span className="text-xs text-gray-500">No tags</span>
        )}
      </div>
    </div>
  );
}


