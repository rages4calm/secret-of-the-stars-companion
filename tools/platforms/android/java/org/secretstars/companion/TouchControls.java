package org.secretstars.companion;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.os.Build;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.FrameLayout;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import java.util.function.IntConsumer;

/** Touch-only controls over the SDL surface. Pointer input outside the HUD passes through. */
final class TouchControls extends FrameLayout {
    private static final int PANEL = 0xe6213039;
    private static final int INK = 0xfff4f9f8;
    private static final int TEAL = 0xff88dbd4;
    private static final int GOLD = 0xffffdb9a;
    private static final int OUTLINE = 0xff627781;
    private static final int[] DIRECTION_KEYS = {KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_RIGHT,
            KeyEvent.KEYCODE_DPAD_DOWN, KeyEvent.KEYCODE_DPAD_LEFT};
    private static final int[] FACE_KEYS = {KeyEvent.KEYCODE_S, KeyEvent.KEYCODE_X,
            KeyEvent.KEYCODE_Z, KeyEvent.KEYCODE_A};
    private static final String[] DIRECTION_GLYPHS = {"\u25b2", "\u25b6", "\u25bc", "\u25c0"};

    private final IntConsumer down;
    private final IntConsumer up;
    private final Consumer<Boolean> visibilityChanged;
    private final Map<Integer, KeyButton> keys = new LinkedHashMap<>();
    private final Set<Integer> held = new HashSet<>();
    private final FrameLayout hud;
    private final DirectionPad directions;
    private final FrameLayout faces;
    private final Button toggle;
    private final Button tools;
    private final FrameLayout shortcuts;
    private final KeyButton[] shortcutKeys;
    private final KeyButton leftShoulder;
    private final KeyButton rightShoulder;
    private final KeyButton start;
    private final KeyButton select;

    TouchControls(Context context, boolean initialShown, IntConsumer down, IntConsumer up,
                  Consumer<Boolean> visibilityChanged) {
        super(context);
        this.down = down;
        this.up = up;
        this.visibilityChanged = visibilityChanged;
        setMotionEventSplittingEnabled(true);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        hud = cluster();
        addView(hud, new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT));
        directions = new DirectionPad(context);
        place(hud, directions, Gravity.LEFT | Gravity.BOTTOM);
        faces = cluster();
        place(hud, faces, Gravity.RIGHT | Gravity.BOTTOM);
        // Keep the SNES's X/Y/A/B positions and the existing native key mapping.
        makeKey(faces, "X", KeyEvent.KEYCODE_S, INK, true, 0);
        makeKey(faces, "A", KeyEvent.KEYCODE_X, GOLD, true, 0);
        makeKey(faces, "B", KeyEvent.KEYCODE_Z, INK, true, 0);
        makeKey(faces, "Y", KeyEvent.KEYCODE_A, INK, true, 0);
        leftShoulder = makeKey(hud, "L", KeyEvent.KEYCODE_C, TEAL, false, 0);
        rightShoulder = makeKey(hud, "R", KeyEvent.KEYCODE_V, TEAL, false, 0);
        start = makeKey(hud, "Start", KeyEvent.KEYCODE_ENTER, INK, false, 0);
        select = makeKey(hud, "Select", KeyEvent.KEYCODE_SHIFT_RIGHT, INK, false, 0);

        tools = new Button(context);
        style(tools, TEAL, false);
        tools.setText("Tools");
        place(hud, tools, Gravity.TOP | Gravity.LEFT);
        shortcuts = cluster();
        place(hud, shortcuts, Gravity.TOP | Gravity.LEFT);
        shortcuts.setVisibility(GONE);
        shortcutKeys = new KeyButton[] {
                makeKey(shortcuts, "Journal", KeyEvent.KEYCODE_J, INK, false, 0),
                makeKey(shortcuts, "Map", KeyEvent.KEYCODE_M, INK, false, 0),
                makeKey(shortcuts, "Boost", KeyEvent.KEYCODE_SHIFT_LEFT, INK, false, 0),
                makeKey(shortcuts, "Turbo", KeyEvent.KEYCODE_TAB, INK, false, 0)
        };
        tools.setOnClickListener(view -> setToolsOpen(shortcuts.getVisibility() != VISIBLE));
        setToolsOpen(false);

        toggle = new Button(context);
        style(toggle, TEAL, false);
        place(this, toggle, Gravity.TOP | Gravity.RIGHT);
        toggle.setOnClickListener(view -> {
            boolean shown = hud.getVisibility() != VISIBLE;
            setShown(shown);
            this.visibilityChanged.accept(shown);
        });
        setShown(initialShown);

        setOnApplyWindowInsetsListener((view, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                Insets safe = insets.getInsets(WindowInsets.Type.systemBars()
                        | WindowInsets.Type.displayCutout() | WindowInsets.Type.systemGestures());
                setPadding(safe.left, safe.top, safe.right, safe.bottom);
            } else {
                setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        requestApplyInsets();
    }

    @Override protected void onDetachedFromWindow() {
        releaseAll();
        super.onDetachedFromWindow();
    }

    void releaseAll() {
        for (KeyButton button : keys.values()) button.cancelPulse();
        for (int key : held) up.accept(key);
        held.clear();
        for (KeyButton button : keys.values()) button.setPressed(false);
        directions.clearPointer();
    }

    private void setShown(boolean shown) {
        if (!shown) {
            releaseAll();
            setToolsOpen(false);
        }
        hud.setVisibility(shown ? VISIBLE : GONE);
        toggle.setText(shown ? "Hide controls" : "Show controls");
    }

    private void setToolsOpen(boolean open) {
        if (!open) {
            for (KeyButton key : shortcutKeys) {
                key.cancelPulse();
                change(key.key, false);
            }
        }
        shortcuts.setVisibility(open ? VISIBLE : GONE);
        tools.setSelected(open);
        tools.setContentDescription(open ? "Close game tools" : "Open game tools");
    }

    private void change(int key, boolean pressed) {
        if (pressed ? held.add(key) : held.remove(key)) {
            keys.get(key).setPressed(pressed);
            (pressed ? down : up).accept(key);
        }
    }

    private FrameLayout cluster() {
        FrameLayout result = new FrameLayout(getContext());
        result.setMotionEventSplittingEnabled(true);
        return result;
    }

    private void place(FrameLayout parent, android.view.View child, int gravity) {
        parent.addView(child, new LayoutParams(0, 0, gravity));
    }

    private KeyButton makeKey(FrameLayout parent, String label, int key, int color,
                              boolean round, int arrow) {
        KeyButton button = new KeyButton(label, key, arrow);
        style(button, color, round);
        keys.put(key, button);
        place(parent, button, Gravity.LEFT | Gravity.TOP);
        return button;
    }

    private void style(Button button, int color, boolean round) {
        button.setAllCaps(false);
        button.setTextColor(color);
        button.setSingleLine();
        button.setEllipsize(TextUtils.TruncateAt.END);
        button.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        button.setTextSize(13);
        button.setAutoSizeTextTypeUniformWithConfiguration(10, 14, 1, TypedValue.COMPLEX_UNIT_SP);
        button.setGravity(Gravity.CENTER);
        button.setPadding(dp(3), 0, dp(3), 0);
        button.setMinWidth(0);
        button.setMinHeight(0);
        button.setMinimumWidth(0);
        button.setMinimumHeight(0);
        button.setSoundEffectsEnabled(false);
        // Accessibility click remains available without stealing hardware D-pad focus from SDL.
        button.setFocusable(false);
        GradientDrawable shape = new GradientDrawable();
        GradientDrawable mask = new GradientDrawable();
        if (round) {
            shape.setShape(GradientDrawable.OVAL);
            mask.setShape(GradientDrawable.OVAL);
        } else {
            shape.setCornerRadius(dp(13));
            mask.setCornerRadius(dp(13));
        }
        shape.setColor(PANEL);
        shape.setStroke(dp(1), color == GOLD ? GOLD : OUTLINE);
        mask.setColor(0xffffffff);
        button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x6669dfd3), shape, mask));
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static void size(android.view.View view, int width, int height, int gravity, int x, int y) {
        LayoutParams params = (LayoutParams) view.getLayoutParams();
        params.width = width;
        params.height = height;
        params.gravity = gravity;
        params.setMargins((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.RIGHT ? 0 : x,
                (gravity & Gravity.VERTICAL_GRAVITY_MASK) == Gravity.BOTTOM ? 0 : y,
                (gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.RIGHT ? x : 0,
                (gravity & Gravity.VERTICAL_GRAVITY_MASK) == Gravity.BOTTOM ? y : 0);
    }

    @Override protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int available = MeasureSpec.getSize(widthMeasureSpec) - getPaddingLeft() - getPaddingRight();
        int height = MeasureSpec.getSize(heightMeasureSpec) - getPaddingTop() - getPaddingBottom();
        int edge = dp(12);
        int gap = dp(8);
        int target = dp(48);
        // Retain two usable thumb regions in narrow split-screen windows.
        int horizontalLimit = (available - 2 * edge - 5 * gap) / 6;
        int verticalLimit = (height - 2 * edge - 2 * target - 2 * gap) / 3;
        int tile = Math.max(dp(36), Math.min(dp(52), Math.min(horizontalLimit, verticalLimit)));
        int step = tile + gap;
        int pad = 3 * tile + 2 * gap;
        int left = Gravity.LEFT | Gravity.BOTTOM;
        int right = Gravity.RIGHT | Gravity.BOTTOM;
        size(directions, pad, pad, left, edge, edge);
        size(faces, pad, pad, right, edge, edge);
        directions.step = step;
        for (int direction = 0; direction < 4; direction++) {
            int column = direction == 1 ? 2 : direction == 3 ? 0 : 1;
            int row = direction == 0 ? 0 : direction == 2 ? 2 : 1;
            size(keys.get(DIRECTION_KEYS[direction]), tile, tile, Gravity.TOP | Gravity.LEFT,
                    column * step, row * step);
            size(keys.get(FACE_KEYS[direction]), tile, tile, Gravity.TOP | Gravity.LEFT,
                    column * step, row * step);
        }
        // Shoulders sit over the outer column, above the face/direction diamond.
        int shoulder = Math.min(dp(74), pad);
        size(leftShoulder, shoulder, target, left, edge, edge + pad);
        size(rightShoulder, shoulder, target, right, edge, edge + pad);
        int systemWidth = dp(59);
        int systemGap = dp(4);
        boolean centerFits = available >= 2 * (edge + pad + systemWidth + systemGap);
        int systemY = centerFits ? edge : height >= dp(310) ? edge + pad + target + gap : target + 2 * edge;
        int systemGravity = !centerFits && height < dp(310) ? Gravity.TOP : Gravity.BOTTOM;
        int center = available / 2;
        size(select, systemWidth, target, Gravity.LEFT | systemGravity, center - systemWidth - systemGap, systemY);
        size(start, systemWidth, target, Gravity.LEFT | systemGravity, center + systemGap, systemY);
        size(toggle, dp(112), target, Gravity.TOP | Gravity.RIGHT, edge, edge);
        size(tools, dp(60), target, Gravity.TOP | Gravity.LEFT, edge, edge);
        int shortcutWidth = dp(70);
        int shortcutStep = shortcutWidth + gap;
        int columns = available >= dp(500) ? 4 : 2;
        size(shortcuts, columns * shortcutStep - gap, (4 / columns) * (target + gap) - gap,
                Gravity.TOP | Gravity.LEFT, edge, edge + target + gap);
        for (int index = 0; index < shortcutKeys.length; index++) {
            size(shortcutKeys[index], shortcutWidth, target, Gravity.TOP | Gravity.LEFT,
                    index % columns * shortcutStep, index / columns * (target + gap));
        }
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
    }

    private final class KeyButton extends Button {
        final int key;
        private final Runnable endPulse;
        private boolean touchClick;

        KeyButton(String label, int key, int arrow) {
            super(TouchControls.this.getContext());
            this.key = key;
            endPulse = () -> change(key, false);
            setContentDescription(label);
            setText(arrow == 0 ? label : DIRECTION_GLYPHS[arrow - 1]);
            setOnClickListener(view -> {
                if (!touchClick && !held.contains(key)) {
                    change(key, true);
                    postDelayed(endPulse, 70);
                }
            });
        }

        void cancelPulse() {
            removeCallbacks(endPulse);
        }

        @Override public boolean onTouchEvent(MotionEvent event) {
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    cancelPulse();
                    change(key, true);
                    return true;
                case MotionEvent.ACTION_UP:
                    change(key, false);
                    touchClick = true;
                    performClick();
                    touchClick = false;
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    change(key, false);
                    return true;
                default:
                    return true;
            }
        }

    }

    private final class DirectionPad extends FrameLayout {
        private int pointer = -1;
        private int mask;
        private int step;

        DirectionPad(Context context) {
            super(context);
            String[] labels = {"Up", "Right", "Down", "Left"};
            for (int i = 0; i < 4; i++) makeKey(this, labels[i], DIRECTION_KEYS[i], TEAL, false, i + 1);
        }

        void clearPointer() {
            pointer = -1;
            mask = 0;
        }

        @Override public boolean onInterceptTouchEvent(MotionEvent event) {
            return event.getActionMasked() == MotionEvent.ACTION_DOWN;
        }

        @Override public boolean onTouchEvent(MotionEvent event) {
            int action = event.getActionMasked();
            int index = event.getActionIndex();
            if (action == MotionEvent.ACTION_DOWN) pointer = event.getPointerId(index);
            if (action == MotionEvent.ACTION_CANCEL || action == MotionEvent.ACTION_UP
                    || action == MotionEvent.ACTION_POINTER_UP && event.getPointerId(index) == pointer) {
                update(0);
                clearPointer();
            } else {
                int current = event.findPointerIndex(pointer);
                if (current != -1) {
                    float x = event.getX(current) - getWidth() / 2f;
                    float y = event.getY(current) - getHeight() / 2f;
                    float deadZone = step / 2f;
                    int next = y < -deadZone ? 1 : y > deadZone ? 4 : 0;
                    next |= x > deadZone ? 2 : x < -deadZone ? 8 : 0;
                    update(next);
                }
            }
            return true;
        }

        private void update(int next) {
            int changed = mask ^ next;
            for (int index = 0; index < DIRECTION_KEYS.length; index++) {
                int bit = 1 << index;
                if ((changed & bit) != 0) {
                    keys.get(DIRECTION_KEYS[index]).cancelPulse();
                    change(DIRECTION_KEYS[index], (next & bit) != 0);
                }
            }
            mask = next;
        }
    }
}
