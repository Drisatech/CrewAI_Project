<?php
/**
 * FarmDepot Voice Assistant WordPress Integration
 * Add this code to your theme's functions.php file
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class FarmDepotVoiceAssistant {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_rest_routes'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('init', array($this, 'create_custom_post_types'));
        add_shortcode('voice_assistant', array($this, 'voice_assistant_shortcode'));
    }
    
    /**
     * Register custom REST API routes
     */
    public function register_rest_routes() {
        // Product search endpoint
        register_rest_route('farmdepot/v1', '/search', array(
            'methods' => 'POST',
            'callback' => array($this, 'search_products'),
            'permission_callback' => '__return_true',
            'args' => array(
                'query' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'category' => array(
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'location' => array(
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'min_price' => array(
                    'required' => false,
                    'type' => 'integer'
                ),
                'max_price' => array(
                    'required' => false,
                    'type' => 'integer'
                )
            )
        ));
        
        // Create product endpoint
        register_rest_route('farmdepot/v1', '/create-product', array(
            'methods' => 'POST',
            'callback' => array($this, 'create_product'),
            'permission_callback' => array($this, 'create_product_permissions'),
            'args' => array(
                'title' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'description' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'wp_kses_post'
                ),
                'price' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'location' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'category' => array(
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                ),
                'contact' => array(
                    'required' => false,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field'
                )
            )
        ));
        
        // User registration endpoint
        register_rest_route('farmdepot/v1', '/register', array(
            'methods' => 'POST',
            'callback' => array($this, 'register_user'),
            'permission_callback' => '__return_true',
            'args' => array(
                'username' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_user'
                ),
                'email' => array(
                    'required' => true,
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_email'
                ),
                'password' => array(
                    'required' => true,
                    'type' => 'string'
                )
            )
        ));
        
        // Voice interaction logging
        register_rest_route('farmdepot/v1', '/log-interaction', array(
            'methods' => 'POST',
            'callback' => array($this, 'log_voice_interaction'),
            'permission_callback' => '__return_true'
        ));
    }
    
    /**
     * Multilingual agricultural terms mapping
     */
    private function get_multilingual_terms() {
        return array(
            'hausa' => array(
                'masara' => 'maize', 'shinkafa' => 'rice', 'rogo' => 'cassava', 'doya' => 'yam',
                'koko' => 'cocoa', 'gyada' => 'groundnut', 'wake' => 'beans', 'gero' => 'millet',
                'dawa' => 'sorghum', 'ayaba' => 'plantain', 'tumatir' => 'tomato', 'barkono' => 'pepper',
                'albasa' => 'onion', 'shanu' => 'cattle', 'akuya' => 'goat', 'kaza' => 'chicken'
            ),
            'igbo' => array(
                'ọka' => 'maize', 'osikapa' => 'rice', 'akpu' => 'cassava', 'ji' => 'yam',
                'koko' => 'cocoa', 'ahụekere' => 'groundnut', 'agwa' => 'beans', 'acha' => 'millet',
                'unere' => 'plantain', 'tomato' => 'tomato', 'ose' => 'pepper', 'yabasị' => 'onion',
                'ehi' => 'cattle', 'ewu' => 'goat', 'ọkụkọ' => 'chicken'
            ),
            'yoruba' => array(
                'agbado' => 'maize', 'iresi' => 'rice', 'gbaguda' => 'cassava', 'isu' => 'yam',
                'koko' => 'cocoa', 'epa' => 'groundnut', 'ewa' => 'beans', 'oka' => 'millet',
                'ọgẹdẹ' => 'plantain', 'tomati' => 'tomato', 'ata' => 'pepper', 'alubosa' => 'onion',
                'malu' => 'cattle', 'ewure' => 'goat', 'adiye' => 'chicken'
            )
        );
    }
    
    /**
     * Translate search terms from local languages to English
     */
    private function translate_search_terms($search_term, $language) {
        if ($language === 'english') {
            return $search_term;
        }
        
        $terms = $this->get_multilingual_terms();
        $search_lower = strtolower($search_term);
        
        if (isset($terms[$language])) {
            foreach ($terms[$language] as $local_term => $english_term) {
                if (strpos($search_lower, $local_term) !== false) {
                    $search_term = str_replace($local_term, $english_term, $search_lower);
                    break;
                }
            }
        }
        
        return $search_term;
    }
        $query = $request->get_param('query');
        $category = $request->get_param('category');
        $location = $request->get_param('location');
        $min_price = $request->get_param('min_price');
        $max_price = $request->get_param('max_price');
        
        // Build search arguments
        $args = array(
            'post_type' => 'farm_product',
            'post_status' => 'publish',
            'posts_per_page' => 20,
            's' => $translated_query, // Use translated query
            'meta_query' => array(
                'relation' => 'AND',
                array(
                    'key' => 'availability',
                    'value' => 'available',
                    'compare' => '='
                )
            )
        );
        
        // Add price range filter
        if ($min_price || $max_price) {
            $price_query = array('key' => 'price');
            
            if ($min_price && $max_price) {
                $price_query['value'] = array($min_price, $max_price);
                $price_query['type'] = 'NUMERIC';
                $price_query['compare'] = 'BETWEEN';
            } elseif ($min_price) {
                $price_query['value'] = $min_price;
                $price_query['type'] = 'NUMERIC';
                $price_query['compare'] = '>=';
            } elseif ($max_price) {
                $price_query['value'] = $max_price;
                $price_query['type'] = 'NUMERIC';
                $price_query['compare'] = '<=';
            }
            
            $args['meta_query'][] = $price_query;
        }
        
        // Add location filter
        if ($location) {
            $args['meta_query'][] = array(
                'key' => 'location',
                'value' => $location,
                'compare' => 'LIKE'
            );
        }
        
        // Add category filter
        if ($category) {
            $args['tax_query'] = array(
                array(
                    'taxonomy' => 'product_category',
                    'field' => 'slug',
                    'terms' => sanitize_title($category)
                )
            );
        }
        
        $posts = get_posts($args);
        $results = array();
        
        foreach ($posts as $post) {
            $meta = get_post_meta($post->ID);
            $categories = get_the_terms($post->ID, 'product_category');
            
            $results[] = array(
                'id' => $post->ID,
                'title' => $post->post_title,
                'description' => wp_trim_words($post->post_content, 30, '...'),
                'price' => isset($meta['price'][0]) ? $meta['price'][0] : '',
                'location' => isset($meta['location'][0]) ? $meta['location'][0] : '',
                'contact' => isset($meta['contact'][0]) ? $meta['contact'][0] : '',
                'availability' => isset($meta['availability'][0]) ? $meta['availability'][0] : 'available',
                'category' => $categories ? $categories[0]->name : '',
                'image' => get_the_post_thumbnail_url($post->ID, 'medium'),
                'permalink' => get_permalink($post->ID),
                'date_posted' => get_the_date('Y-m-d', $post->ID)
            );
        }
        
        // Log the search for analytics
        $this->log_product_search($query, count($results));
        
        return new WP_REST_Response(array(
            'success' => true,
            'count' => count($results),
            'query' => $query,
            'results' => $results
        ), 200);
    }
    
    /**
     * Create a new product listing
     */
    public function create_product($request) {
        $title = $request->get_param('title');
        $description = $request->get_param('description');
        $price = $request->get_param('price');
        $location = $request->get_param('location');
        $category = $request->get_param('category');
        $contact = $request->get_param('contact');
        
        // Get current user
        $current_user = wp_get_current_user();
        
        // Create post data
        $post_data = array(
            'post_title' => $title,
            'post_content' => $description,
            'post_type' => 'farm_product',
            'post_status' => 'pending', // Moderate new listings
            'post_author' => $current_user->ID
        );
        
        $post_id = wp_insert_post($post_data);
        
        if (is_wp_error($post_id)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Failed to create product listing'
            ), 400);
        }
        
        // Add meta data
        update_post_meta($post_id, 'price', sanitize_text_field($price));
        update_post_meta($post_id, 'location', sanitize_text_field($location));
        update_post_meta($post_id, 'contact', sanitize_text_field($contact ?: $current_user->user_email));
        update_post_meta($post_id, 'availability', 'available');
        update_post_meta($post_id, 'created_via', 'voice_assistant');
        
        // Set category if provided
        if ($category) {
            $term = get_term_by('name', $category, 'product_category');
            if (!$term) {
                $term = wp_insert_term($category, 'product_category');
                if (!is_wp_error($term)) {
                    wp_set_post_terms($post_id, $term['term_id'], 'product_category');
                }
            } else {
                wp_set_post_terms($post_id, $term->term_id, 'product_category');
            }
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'Product listing created successfully and is pending review',
            'post_id' => $post_id,
            'edit_link' => admin_url('post.php?post=' . $post_id . '&action=edit')
        ), 201);
    }
    
    /**
     * Register new user
     */
    public function register_user($request) {
        $username = $request->get_param('username');
        $email = $request->get_param('email');
        $password = $request->get_param('password');
        
        // Validate email
        if (!is_email($email)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Please provide a valid email address'
            ), 400);
        }
        
        // Check if username exists
        if (username_exists($username)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Username already exists'
            ), 400);
        }
        
        // Check if email exists
        if (email_exists($email)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Email address already registered'
            ), 400);
        }
        
        // Create user
        $user_id = wp_create_user($username, $password, $email);
        
        if (is_wp_error($user_id)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => $user_id->get_error_message()
            ), 400);
        }
        
        // Set user role
        $user = new WP_User($user_id);
        $user->set_role('subscriber');
        
        // Add meta data
        update_user_meta($user_id, 'registered_via', 'voice_assistant');
        update_user_meta($user_id, 'registration_date', current_time('mysql'));
        
        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'User registered successfully',
            'user_id' => $user_id,
            'username' => $username
        ), 201);
    }
    
    /**
     * Log voice interactions for analytics
     */
    public function log_voice_interaction($request) {
        global $wpdb;
        
        $command = sanitize_text_field($request->get_param('command'));
        $response = sanitize_textarea_field($request->get_param('response'));
        $intent = sanitize_text_field($request->get_param('intent'));
        $confidence = floatval($request->get_param('confidence'));
        $processing_time = floatval($request->get_param('processing_time'));
        
        $table_name = $wpdb->prefix . 'voice_interactions';
        
        $result = $wpdb->insert(
            $table_name,
            array(
                'user_id' => get_current_user_id(),
                'session_id' => session_id(),
                'command_text' => $command,
                'response_text' => $response,
                'intent' => $intent,
                'confidence_score' => $confidence,
                'processing_time' => $processing_time,
                'created_at' => current_time('mysql')
            ),
            array('%d', '%s', '%s', '%s', '%s', '%f', '%f', '%s')
        );
        
        return new WP_REST_Response(array(
            'success' => $result !== false,
            'logged' => $result !== false
        ), 200);
    }
    
    /**
     * Log product searches for analytics
     */
    private function log_product_search($search_term, $results_count) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'voice_product_searches';
        
        $wpdb->insert(
            $table_name,
            array(
                'search_term' => $search_term,
                'results_count' => $results_count,
                'user_location' => $this->get_user_location(),
                'created_at' => current_time('mysql')
            ),
            array('%s', '%d', '%s', '%s')
        );
    }
    
    /**
     * Get user location (placeholder - implement geolocation)
     */
    private function get_user_location() {
        // Implement geolocation logic here
        return 'Unknown';
    }
    
    /**
     * Permission callback for creating products
     */
    public function create_product_permissions($request) {
        return is_user_logged_in();
    }
    
    /**
     * Create custom post types
     */
    public function create_custom_post_types() {
        // Farm products post type
        register_post_type('farm_product', array(
            'labels' => array(
                'name' => 'Farm Products',
                'singular_name' => 'Farm Product',
                'add_new' => 'Add New Product',
                'add_new_item' => 'Add New Farm Product',
                'edit_item' => 'Edit Farm Product',
                'new_item' => 'New Farm Product',
                'view_item' => 'View Farm Product',
                'search_items' => 'Search Farm Products',
                'not_found' => 'No farm products found',
                'not_found_in_trash' => 'No farm products found in trash'
            ),
            'public' => true,
            'has_archive' => true,
            'rewrite' => array('slug' => 'products'),
            'supports' => array('title', 'editor', 'thumbnail', 'excerpt'),
            'menu_icon' => 'dashicons-carrot',
            'show_in_rest' => true
        ));
        
        // Product categories taxonomy
        register_taxonomy('product_category', 'farm_product', array(
            'labels' => array(
                'name' => 'Product Categories',
                'singular_name' => 'Product Category',
                'search_items' => 'Search Categories',
                'all_items' => 'All Categories',
                'edit_item' => 'Edit Category',
                'update_item' => 'Update Category',
                'add_new_item' => 'Add New Category',
                'new_item_name' => 'New Category Name'
            ),
            'hierarchical' => true,
            'show_ui' => true,
            'show_in_rest' => true,
            'rewrite' => array('slug' => 'product-category')
        ));
    }
    
    /**
     * Enqueue necessary scripts and styles
     */
    public function enqueue_scripts() {
        wp_enqueue_script('jquery');
        
        wp_localize_script('jquery', 'farmdepot_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'rest_url' => rest_url('farmdepot/v1/'),
            'nonce' => wp_create_nonce('wp_rest')
        ));
    }
    
    /**
     * Shortcode for embedding voice assistant
     */
    public function voice_assistant_shortcode($atts) {
        $atts = shortcode_atts(array(
            'height' => '600px',
            'width' => '100%'
        ), $atts);
        
        $voice_assistant_url = site_url('/voice-assistant/');
        
        return '<div class="voice-assistant-container">
                    <iframe src="' . esc_url($voice_assistant_url) . '" 
                            width="' . esc_attr($atts['width']) . '" 
                            height="' . esc_attr($atts['height']) . '" 
                            frameborder="0">
                    </iframe>
                </div>';
    }
}

// Initialize the voice assistant integration
new FarmDepotVoiceAssistant();

/**
 * Create database tables on activation
 */
function create_voice_assistant_tables() {
    global $wpdb;
    
    $charset_collate = $wpdb->get_charset_collate();
    
    // Voice interactions table
    $table_name = $wpdb->prefix . 'voice_interactions';
    $sql = "CREATE TABLE $table_name (
        id int(11) NOT NULL AUTO_INCREMENT,
        user_id int(11) DEFAULT NULL,
        session_id varchar(100) DEFAULT NULL,
        command_text text NOT NULL,
        response_text text,
        intent varchar(50),
        confidence_score decimal(3,2) DEFAULT 0.00,
        processing_time decimal(5,2) DEFAULT 0.00,
        created_at timestamp DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY user_id (user_id),
        KEY intent (intent),
        KEY created_at (created_at)
    ) $charset_collate;";
    
    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    dbDelta($sql);
    
    // Product searches table
    $table_name = $wpdb->prefix . 'voice_product_searches';
    $sql = "CREATE TABLE $table_name (
        id int(11) NOT NULL AUTO_INCREMENT,
        search_term varchar(255) NOT NULL,
        results_count int(11) DEFAULT 0,
        user_location varchar(100),
        created_at timestamp DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY search_term (search_term),
        KEY created_at (created_at)
    ) $charset_collate;";
    
    dbDelta($sql);
}

// Hook to create tables (run this once during setup)
register_activation_hook(__FILE__, 'create_voice_assistant_tables');

/**
 * Add custom meta boxes for farm products
 */
function add_farm_product_meta_boxes() {
    add_meta_box(
        'farm_product_details',
        'Product Details',
        'farm_product_meta_box_callback',
        'farm_product',
        'normal',
        'high'
    );
}
add_action('add_meta_boxes', 'add_farm_product_meta_boxes');

function farm_product_meta_box_callback($post) {
    wp_nonce_field('farm_product_meta_box', 'farm_product_meta_box_nonce');
    
    $price = get_post_meta($post->ID, 'price', true);
    $location = get_post_meta($post->ID, 'location', true);
    $contact = get_post_meta($post->ID, 'contact', true);
    $availability = get_post_meta($post->ID, 'availability', true);
    
    echo '<table class="form-table">';
    echo '<tr>';
    echo '<th><label for="price">Price (₦)</label></th>';
    echo '<td><input type="text" id="price" name="price" value="' . esc_attr($price) . '" /></td>';
    echo '</tr>';
    echo '<tr>';
    echo '<th><label for="location">Location</label></th>';
    echo '<td><input type="text" id="location" name="location" value="' . esc_attr($location) . '" /></td>';
    echo '</tr>';
    echo '<tr>';
    echo '<th><label for="contact">Contact Info</label></th>';
    echo '<td><input type="text" id="contact" name="contact" value="' . esc_attr($contact) . '" /></td>';
    echo '</tr>';
    echo '<tr>';
    echo '<th><label for="availability">Availability</label></th>';
    echo '<td>';
    echo '<select id="availability" name="availability">';
    echo '<option value="available"' . selected($availability, 'available', false) . '>Available</option>';
    echo '<option value="sold"' . selected($availability, 'sold', false) . '>Sold</option>';
    echo '<option value="reserved"' . selected($availability, 'reserved', false) . '>Reserved</option>';
    echo '</select>';
    echo '</td>';
    echo '</tr>';
    echo '</table>';
}

function save_farm_product_meta_box($post_id) {
    if (!isset($_POST['farm_product_meta_box_nonce'])) {
        return;
    }
    
    if (!wp_verify_nonce($_POST['farm_product_meta_box_nonce'], 'farm_product_meta_box')) {
        return;
    }
    
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }
    
    if (!current_user_can('edit_post', $post_id)) {
        return;
    }
    
    if (isset($_POST['price'])) {
        update_post_meta($post_id, 'price', sanitize_text_field($_POST['price']));
    }
    
    if (isset($_POST['location'])) {
        update_post_meta($post_id, 'location', sanitize_text_field($_POST['location']));
    }
    
    if (isset($_POST['contact'])) {
        update_post_meta($post_id, 'contact', sanitize_text_field($_POST['contact']));
    }
    
    if (isset($_POST['availability'])) {
        update_post_meta($post_id, 'availability', sanitize_text_field($_POST['availability']));
    }
}
add_action('save_post', 'save_farm_product_meta_box');

/**
 * Add default product categories
 */
function create_default_product_categories() {
    $categories = array(
        'Grains & Cereals' => array('Maize', 'Rice', 'Wheat', 'Millet', 'Sorghum'),
        'Root Crops' => array('Cassava', 'Yam', 'Sweet Potato', 'Irish Potato', 'Cocoyam'),
        'Legumes' => array('Beans', 'Groundnut', 'Cowpea', 'Soybean', 'Bambara Nut'),
        'Vegetables' => array('Tomato', 'Pepper', 'Onion', 'Okra', 'Spinach', 'Cucumber'),
        'Fruits' => array('Orange', 'Mango', 'Banana', 'Pineapple', 'Watermelon', 'Pawpaw'),
        'Cash Crops' => array('Cocoa', 'Coffee', 'Oil Palm', 'Rubber', 'Cotton'),
        'Livestock' => array('Cattle', 'Goats', 'Sheep', 'Poultry', 'Pigs', 'Fish'),
        'Farm Equipment' => array('Tractors', 'Harvesters', 'Ploughs', 'Sprayers', 'Irrigation'),
        'Seeds & Seedlings' => array('Crop Seeds', 'Vegetable Seeds', 'Tree Seedlings', 'Flower Seeds'),
        'Farm Inputs' => array('Fertilizers', 'Pesticides', 'Herbicides', 'Farm Tools')
    );
    
    foreach ($categories as $parent_name => $children) {
        // Create parent category
        $parent_term = wp_insert_term($parent_name, 'product_category');
        
        if (!is_wp_error($parent_term)) {
            $parent_id = $parent_term['term_id'];
            
            // Create child categories
            foreach ($children as $child_name) {
                wp_insert_term($child_name, 'product_category', array(
                    'parent' => $parent_id
                ));
            }
        }
    }
}

// Run once to create default categories
// create_default_product_categories();

/**
 * CORS headers for API requests
 */
function add_cors_http_header() {
    header("Access-Control-Allow-Origin: *");
    header("Access-Control-Allow-Methods: GET, POST, OPTIONS, PUT, DELETE");
    header("Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept, Authorization, Cache-Control");
}
add_action('init', 'add_cors_http_header');

/**
 * Custom search functionality for voice queries
 */
function enhanced_voice_search($query_vars) {
    if (isset($query_vars['voice_search']) && $query_vars['voice_search']) {
        $search_term = sanitize_text_field($query_vars['s']);
        
        // Nigerian agricultural terms mapping
        $term_mapping = array(
            'corn' => 'maize',
            'guinea corn' => 'sorghum',
            'groundnuts' => 'groundnut',
            'peanuts' => 'groundnut',
            'irish potato' => 'potato',
            'sweet potato' => 'sweet potato',
            'cocoyam' => 'taro',
            'plantain' => 'banana',
            'fowl' => 'poultry',
            'chicken' => 'poultry',
            'cow' => 'cattle',
            'bull' => 'cattle',
            'ox' => 'cattle'
        );
        
        // Replace terms if mapping exists
        if (isset($term_mapping[strtolower($search_term)])) {
            $query_vars['s'] = $term_mapping[strtolower($search_term)];
        }
        
        // Add meta query for availability
        $query_vars['meta_query'] = array(
            array(
                'key' => 'availability',
                'value' => 'available',
                'compare' => '='
            )
        );
    }
    
    return $query_vars;
}
add_filter('pre_get_posts', function($query) {
    if (!is_admin() && $query->is_main_query()) {
        if (isset($_GET['voice_search'])) {
            $query->set('voice_search', true);
            $query = enhanced_voice_search($query->query_vars);
        }
    }
    return $query;
});

/**
 * Analytics dashboard for voice interactions
 */
function voice_assistant_analytics_page() {
    global $wpdb;
    
    // Get interaction statistics
    $interactions_table = $wpdb->prefix . 'voice_interactions';
    $searches_table = $wpdb->prefix . 'voice_product_searches';
    
    $total_interactions = $wpdb->get_var("SELECT COUNT(*) FROM $interactions_table");
    $total_searches = $wpdb->get_var("SELECT COUNT(*) FROM $searches_table");
    
    // Get top search terms
    $top_searches = $wpdb->get_results(
        "SELECT search_term, COUNT(*) as count 
         FROM $searches_table 
         GROUP BY search_term 
         ORDER BY count DESC 
         LIMIT 10"
    );
    
    // Get interaction trends
    $daily_interactions = $wpdb->get_results(
        "SELECT DATE(created_at) as date, COUNT(*) as count 
         FROM $interactions_table 
         WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
         GROUP BY DATE(created_at) 
         ORDER BY date DESC"
    );
    
    ?>
    <div class="wrap">
        <h1>Voice Assistant Analytics</h1>
        
        <div class="dashboard-widgets-wrap">
            <div class="dashboard-widgets">
                <div class="postbox-container" style="width: 49%; float: left;">
                    <div class="postbox">
                        <h2 class="hndle">Overview</h2>
                        <div class="inside">
                            <p><strong>Total Voice Interactions:</strong> <?php echo number_format($total_interactions); ?></p>
                            <p><strong>Total Product Searches:</strong> <?php echo number_format($total_searches); ?></p>
                            <p><strong>Average Daily Interactions:</strong> 
                                <?php echo $total_interactions > 0 ? number_format($total_interactions / 30, 1) : 0; ?>
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="postbox-container" style="width: 49%; float: right;">
                    <div class="postbox">
                        <h2 class="hndle">Top Search Terms</h2>
                        <div class="inside">
                            <?php if ($top_searches): ?>
                                <ol>
                                    <?php foreach ($top_searches as $search): ?>
                                        <li><?php echo esc_html($search->search_term); ?> 
                                            <span style="color: #666;">(<?php echo $search->count; ?> searches)</span>
                                        </li>
                                    <?php endforeach; ?>
                                </ol>
                            <?php else: ?>
                                <p>No search data available yet.</p>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
                
                <div style="clear: both;"></div>
                
                <div class="postbox-container" style="width: 100%;">
                    <div class="postbox">
                        <h2 class="hndle">Daily Interactions (Last 30 Days)</h2>
                        <div class="inside">
                            <?php if ($daily_interactions): ?>
                                <canvas id="interactionsChart" width="400" height="200"></canvas>
                                <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
                                <script>
                                const ctx = document.getElementById('interactionsChart').getContext('2d');
                                const chart = new Chart(ctx, {
                                    type: 'line',
                                    data: {
                                        labels: [<?php echo implode(',', array_map(function($item) { 
                                            return '"' . $item->date . '"'; 
                                        }, array_reverse($daily_interactions))); ?>],
                                        datasets: [{
                                            label: 'Voice Interactions',
                                            data: [<?php echo implode(',', array_map(function($item) { 
                                                return $item->count; 
                                            }, array_reverse($daily_interactions))); ?>],
                                            borderColor: 'rgb(75, 192, 192)',
                                            tension: 0.1
                                        }]
                                    },
                                    options: {
                                        responsive: true,
                                        scales: {
                                            y: {
                                                beginAtZero: true
                                            }
                                        }
                                    }
                                });
                                </script>
                            <?php else: ?>
                                <p>No interaction data available for the last 30 days.</p>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <?php
}

/**
 * Add analytics page to admin menu
 */
function add_voice_assistant_menu() {
    add_menu_page(
        'Voice Assistant Analytics',
        'Voice Analytics',
        'manage_options',
        'voice-assistant-analytics',
        'voice_assistant_analytics_page',
        'dashicons-microphone',
        30
    );
}
add_action('admin_menu', 'add_voice_assistant_menu');

/**
 * Nigerian states for location filtering
 */
function get_nigerian_states() {
    return array(
        'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
        'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe',
        'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara',
        'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau',
        'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
    );
}

/**
 * Add Nigerian states as location options in admin
 */
function add_location_meta_box_with_states() {
    $states = get_nigerian_states();
    // This would be used in the meta box callback to provide a dropdown
}

/**
 * WhatsApp integration for contact
 */
function format_whatsapp_link($phone_number, $message = '') {
    // Clean phone number
    $phone = preg_replace('/[^0-9]/', '', $phone_number);
    
    // Add Nigerian country code if not present
    if (substr($phone, 0, 3) !== '234' && substr($phone, 0, 1) === '0') {
        $phone = '234' . substr($phone, 1);
    }
    
    $encoded_message = urlencode($message);
    return "https://wa.me/{$phone}?text={$encoded_message}";
}

/**
 * Custom endpoint for WhatsApp integration
 */
function register_whatsapp_endpoint() {
    register_rest_route('farmdepot/v1', '/whatsapp-contact', array(
        'methods' => 'POST',
        'callback' => function($request) {
            $phone = sanitize_text_field($request->get_param('phone'));
            $product_title = sanitize_text_field($request->get_param('product_title'));
            $message = "Hi! I'm interested in your {$product_title} listed on FarmDepot.ng. Is it still available?";
            
            $whatsapp_link = format_whatsapp_link($phone, $message);
            
            return new WP_REST_Response(array(
                'success' => true,
                'whatsapp_link' => $whatsapp_link
            ), 200);
        },
        'permission_callback' => '__return_true'
    ));
}
add_action('rest_api_init', 'register_whatsapp_endpoint');

?>