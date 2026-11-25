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
    link.style.cssText =
      'display:block;color:#087b60;font-weight:bold;margin:12px 0;';
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

    const snapshot = JSON.stringify(posts);

    if (container.dataset.snapshot === snapshot) {
      return;
    }

    const videos = container.querySelectorAll('video');

    if ([...videos].some(video => !video.paused && !video.ended)) {
      return;
    }

    const fragment = document.createDocumentFragment();

    if (!posts.length) {
      const card = document.createElement('article');
      card.className = 'card';
      add(card, 'h3', 'No updates yet');
      fragment.append(card);
    }

    posts.forEach(post => {
      const card = document.createElement('article');
      card.className = 'card';
      card.style.minWidth = '0';

      const imageURL = safeURL(post.image_url);
      const videoURL = safeURL(post.video_url);

      if (videoURL) {
        const video = document.createElement('video');

        video.src = videoURL;
        video.controls = true;
        video.playsInline = true;
        video.preload = 'none';

        video.setAttribute('playsinline', '');
        video.setAttribute(
          'aria-label',
          post.title || 'AFROEURO video'
        );

        if (imageURL) {
          video.poster = imageURL;
        }

        video.style.cssText = `
          display:block;
          width:100%;
          aspect-ratio:16/9;
          object-fit:contain;
          background:#071b2b;
          border-radius:12px;
          margin-bottom:14px;
        `;

        card.append(video);

      } else if (imageURL) {
        const image = document.createElement('img');

        image.src = imageURL;
        image.alt = post.title || '';
        image.loading = 'lazy';

        image.style.cssText = `
          display:block;
          width:100%;
          border-radius:12px;
          margin-bottom:12px;
        `;

        card.append(image);
      }

      add(card, 'span', post.category || 'News', 'chip');
      add(card, 'h3', post.title || '');

      const description = add(
        card,
        'p',
        post.description || ''
      );

      description.style.cssText =
        'line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere;';

      if (videoURL) {
        addLink(card, videoURL, 'Open video separately →');
      }

      addLink(card, post.link_url, 'Read more →');

      fragment.append(card);
    });

    container.replaceChildren(fragment);
    container.dataset.snapshot = snapshot;

  } catch (error) {
    if (!container.dataset.snapshot) {
      container.textContent =
        'Community updates temporarily unavailable.';
    }

    console.error(error);
  }
}

function startCommunityPosts() {
  loadCommunityPosts();
  setInterval(loadCommunityPosts, 60000);
}

if (document.readyState === 'loading') {
  document.addEventListener(
    'DOMContentLoaded',
    startCommunityPosts
  );
} else {
  startCommunityPosts();
}
