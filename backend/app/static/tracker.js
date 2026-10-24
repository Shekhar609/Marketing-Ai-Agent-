/**
 * AIPNT Autonomous Revenue Operations - Client Website Tracker
 * Lightweight zero-dependency visitor and lead attribution tracker.
 */
(function(window, document) {
    'use strict';

    var trackerConfig = {
        orgId: null,
        apiEndpoint: '/api/v1/integrations/webhook/website',
        visitorId: null,
        sessionId: null,
    };

    function getOrCreateVisitorId() {
        var vid = localStorage.getItem('aipnt_vid');
        if (!vid) {
            vid = 'vis_' + Math.random().toString(36).substring(2, 12) + '_' + Date.now();
            localStorage.setItem('aipnt_vid', vid);
        }
        return vid;
    }

    function getOrCreateSessionId() {
        var sid = sessionStorage.getItem('aipnt_sid');
        if (!sid) {
            sid = 'ses_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
            sessionStorage.setItem('aipnt_sid', sid);
        }
        return sid;
    }

    function sendEvent(eventType, payload) {
        if (!trackerConfig.orgId) return;

        var fullPayload = {
            organization_id: trackerConfig.orgId,
            event_type: eventType,
            payload: Object.assign({
                visitor_id: trackerConfig.visitorId,
                session_id: trackerConfig.sessionId,
                url: window.location.href,
                path: window.location.pathname,
                referrer: document.referrer || 'direct',
                title: document.title,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
            }, payload || {})
        };

        if (navigator.sendBeacon) {
            navigator.sendBeacon(trackerConfig.apiEndpoint, JSON.stringify(fullPayload));
        } else {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', trackerConfig.apiEndpoint, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(fullPayload));
        }
    }

    // Public API
    window.aipnt = function(action, arg1, arg2) {
        if (action === 'init') {
            trackerConfig.orgId = arg1.orgId;
            if (arg1.apiEndpoint) trackerConfig.apiEndpoint = arg1.apiEndpoint;
            trackerConfig.visitorId = getOrCreateVisitorId();
            trackerConfig.sessionId = getOrCreateSessionId();
        } else if (action === 'track') {
            sendEvent(arg1, arg2);
        } else if (action === 'lead') {
            sendEvent('lead_captured', arg1);
        }
    };

    // Auto capture forms with [data-aipnt-form] or standard lead forms
    document.addEventListener('submit', function(e) {
        var form = e.target;
        var emailInput = form.querySelector('input[type="email"], input[name="email"]');
        if (emailInput && emailInput.value) {
            var nameInput = form.querySelector('input[name="name"], input[name="first_name"]');
            var companyInput = form.querySelector('input[name="company"]');
            window.aipnt('lead', {
                email: emailInput.value,
                name: nameInput ? nameInput.value : '',
                company: companyInput ? companyInput.value : ''
            });
        }
    });

})(window, document);
