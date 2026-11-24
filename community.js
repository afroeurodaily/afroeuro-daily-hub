async function loadCommunityPosts() {
  const container = document.getElementById('published-items');
  if (!container) return;

  const url = 'https://krabepxsqparvpndalhq.supabase.co';
  const key = 'sb_publishable_AlhuoRLK4PAZUxnkuBpVhg_f1uZTk17';

  function safeURL(value) {
    try {
      const u = new URL(value);
      return u.protocol === 'https:' ? u.href : null;
    } catch {
      return null;
    }
  }

  function add(parent, tag, text, cls) {
    const el = document.createElement(tag);
    el.textContent = text;
    if (cls) el.className = cls;
    parent.append(el);
    return el;
  }

  function addLink(card, value, label) {
    const href = safeURL(value);
    if (!href) return;
    const link = add(card, 'a', label);
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.style.cssText = 'display:block;color:#087b60;font-weight:bold;margin:12px 0;';
  }

  try {
    const response = await fetch(
      url + '/rest/v1/posts?select=category,title,description,image_url,video_url,link_url&published=eq.true&order=created_at.desc&limit=50',
      {
        headers: { apikey: key },
        cache: 'no-store'
      }
    );

    if (!response.ok) {
      throw new Error('Unable to load posts');
    }

    const posts = await response.json();
    container.replaceChildren();

    if (!posts.length) {
      const card = document.createElement('article');
      card.className = 'card';
      add(card, 'h3', 'No updates yet');
      container.append(card);
      return;
    }

    posts.forEach(post => {
      const card = document.createElement('article');
      card.className = 'card';

      const imageURL = safeURL(post.image_url);

      if (imageURL) {
        const image = document.createElement('img');
        image.src = imageURL;
        image.alt = post.title || '';
        image.loading = 'lazy';
        image.style.cssText = 'width:100%;border-radius:12px;margin-bottom:12px;';
        card.append(image);
      }

      add(card, 'span', post.category || 'News', 'chip');
      add(card, 'h3', post.title || '');
      add(card, 'p', post.description || '');

      addLink(card, post.video_url, 'Watch video →');
      addLink(card, post.link_url, 'Read more →');

      container.append(card);
    });

  } catch (error) {
    container.textContent = 'Community updates temporarily unavailable.';
    console.error(error);
  }
}

function startCommunityPosts() {
  loadCommunityPosts();
  setInterval(loadCommunityPosts, 60000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startCommunityPosts);
} else {
  startCommunityPosts();
}
