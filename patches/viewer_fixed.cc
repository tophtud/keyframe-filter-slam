// viewer.cc의 load_selected_keyframes와 draw_selected_keyframes 함수만 수정
// 전체 파일이 아닌 수정할 함수만 제공

bool viewer::load_selected_keyframes(const std::string& json_path) {
    std::cout << "[INFO] Loading waypoints from: " << json_path << std::endl;
    std::lock_guard<std::mutex> lock(mtx_selected_keyframes_);
    selected_keyframe_ids_.clear();
    selected_waypoints_.clear();
    
    std::ifstream file(json_path);
    if (!file.is_open()) {
        std::cerr << "[ERROR] Failed to open JSON file: " << json_path << std::endl;
        return false;
    }
    
    // JSON 전체 읽기
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string json_str = buffer.str();
    file.close();
    
    // "waypoints" 배열 찾기
    size_t waypoints_pos = json_str.find("\"waypoints\"");
    if (waypoints_pos == std::string::npos) {
        std::cerr << "[ERROR] No 'waypoints' field found in JSON" << std::endl;
        return false;
    }
    
    std::cout << "[INFO] Parsing waypoints with grid center positions..." << std::endl;
    
    // 간단한 파싱: "id": 값, "position": {"x": 값, "y": 값, "z": 값} 패턴 찾기
    size_t pos = 0;
    int waypoint_count = 0;
    
    while (true) {
        // "id" 필드 찾기
        size_t id_pos = json_str.find("\"id\":", pos);
        if (id_pos == std::string::npos || id_pos < waypoints_pos) {
            break;
        }
        
        // ID 값 추출
        size_t id_value_start = id_pos + 5;  // "id":의 길이
        while (id_value_start < json_str.length() && std::isspace(json_str[id_value_start])) {
            id_value_start++;
        }
        
        size_t id_value_end = id_value_start;
        while (id_value_end < json_str.length() && std::isdigit(json_str[id_value_end])) {
            id_value_end++;
        }
        
        if (id_value_start >= id_value_end) {
            pos = id_pos + 1;
            continue;
        }
        
        unsigned int id = std::stoi(json_str.substr(id_value_start, id_value_end - id_value_start));
        
        // "position" 필드 찾기 (id 다음에 나오는 첫 번째 position)
        size_t pos_pos = json_str.find("\"position\":", id_pos);
        if (pos_pos == std::string::npos) {
            pos = id_pos + 1;
            continue;
        }
        
        // x, y, z 값 추출
        size_t x_pos = json_str.find("\"x\":", pos_pos);
        size_t y_pos = json_str.find("\"y\":", pos_pos);
        size_t z_pos = json_str.find("\"z\":", pos_pos);
        
        if (x_pos == std::string::npos || y_pos == std::string::npos || z_pos == std::string::npos) {
            pos = pos_pos + 1;
            continue;
        }
        
        // x 값
        size_t x_value_start = x_pos + 4;
        while (x_value_start < json_str.length() && std::isspace(json_str[x_value_start])) {
            x_value_start++;
        }
        size_t x_value_end = x_value_start;
        while (x_value_end < json_str.length() && 
               (std::isdigit(json_str[x_value_end]) || json_str[x_value_end] == '.' || 
                json_str[x_value_end] == '-' || json_str[x_value_end] == 'e' || json_str[x_value_end] == 'E')) {
            x_value_end++;
        }
        
        // y 값
        size_t y_value_start = y_pos + 4;
        while (y_value_start < json_str.length() && std::isspace(json_str[y_value_start])) {
            y_value_start++;
        }
        size_t y_value_end = y_value_start;
        while (y_value_end < json_str.length() && 
               (std::isdigit(json_str[y_value_end]) || json_str[y_value_end] == '.' || 
                json_str[y_value_end] == '-' || json_str[y_value_end] == 'e' || json_str[y_value_end] == 'E')) {
            y_value_end++;
        }
        
        // z 값
        size_t z_value_start = z_pos + 4;
        while (z_value_start < json_str.length() && std::isspace(json_str[z_value_start])) {
            z_value_start++;
        }
        size_t z_value_end = z_value_start;
        while (z_value_end < json_str.length() && 
               (std::isdigit(json_str[z_value_end]) || json_str[z_value_end] == '.' || 
                json_str[z_value_end] == '-' || json_str[z_value_end] == 'e' || json_str[z_value_end] == 'E')) {
            z_value_end++;
        }
        
        try {
            double x = std::stod(json_str.substr(x_value_start, x_value_end - x_value_start));
            double y = std::stod(json_str.substr(y_value_start, y_value_end - y_value_start));
            double z = std::stod(json_str.substr(z_value_start, z_value_end - z_value_start));
            
            WaypointInfo wp;
            wp.id = id;
            wp.position = Eigen::Vector3d(x, y, z);
            selected_waypoints_.push_back(wp);
            selected_keyframe_ids_.insert(id);
            
            waypoint_count++;
            
            std::cout << "[DEBUG] Waypoint " << waypoint_count << ": ID=" << id 
                      << ", pos=(" << x << ", " << y << ", " << z << ")" << std::endl;
        }
        catch (const std::exception& e) {
            std::cerr << "[WARN] Failed to parse waypoint: " << e.what() << std::endl;
        }
        
        pos = z_pos + 1;
    }
    
    std::cout << "[SUCCESS] Loaded " << selected_waypoints_.size() 
              << " waypoints with grid center positions" << std::endl;
    
    // Update menu count
    if (menu_selected_keyframe_count_) {
        *menu_selected_keyframe_count_ = static_cast<int>(selected_keyframe_ids_.size());
    }
    
    return !selected_waypoints_.empty();
}

void viewer::draw_selected_keyframes() {
    std::lock_guard<std::mutex> lock(mtx_selected_keyframes_);
    
    // Debug output
    static int debug_count = 0;
    if (debug_count++ % 100 == 0) {
        std::cout << "[DEBUG] draw_selected_keyframes: waypoints=" 
                  << selected_waypoints_.size() << ", keyframe_ids=" 
                  << selected_keyframe_ids_.size() << std::endl;
    }
    
    glPointSize(25.0f);
    glBegin(GL_POINTS);
    glColor3f(1.0f, 0.0f, 0.0f);  // RED
    
    // If we have waypoint positions (grid-center), use them
    if (!selected_waypoints_.empty()) {
        for (const auto& wp : selected_waypoints_) {
            glVertex3d(wp.position.x(), wp.position.y(), wp.position.z());
        }
    }
    else if (!selected_keyframe_ids_.empty()) {
        // Otherwise, use keyframe positions
        auto keyfrms = data_->get_keyframes();
        for (const auto& kf : keyfrms) {
            if (selected_keyframe_ids_.find(kf->id_) != selected_keyframe_ids_.end()) {
                const auto pos = kf->get_trans_wc();
                glVertex3d(pos.x(), pos.y(), pos.z());
            }
        }
    }
    
    glEnd();
}
