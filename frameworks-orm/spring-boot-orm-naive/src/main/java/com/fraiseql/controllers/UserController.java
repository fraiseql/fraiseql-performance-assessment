package com.fraiseql.controllers;

import com.fraiseql.entities.User;
import com.fraiseql.repositories.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/users")
public class UserController {

    private final UserRepository userRepository;

    public UserController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {
        List<User> users = userRepository.findAll();
        return ResponseEntity.ok(users);
    }

    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        Optional<User> user = userRepository.findById(id);
        return user.map(ResponseEntity::ok)
                  .orElse(ResponseEntity.notFound().build());
    }

    // NAIVE: This endpoint demonstrates N+1 query problem!
    // Each call to user.getPosts() triggers a separate query
    @GetMapping("/{id}/with-posts")
    public ResponseEntity<User> getUserWithPosts(@PathVariable Long id) {
        Optional<User> user = userRepository.findById(id);
        if (user.isPresent()) {
            // NAIVE: This triggers N+1 queries when posts are accessed
            List<?> posts = user.get().getPosts(); // Each access = 1 query!
            return ResponseEntity.ok(user.get());
        }
        return ResponseEntity.notFound().build();
    }

    // NAIVE: Even worse - multiple levels of N+1 queries!
    @GetMapping("/{id}/with-posts-and-comments")
    public ResponseEntity<User> getUserWithPostsAndComments(@PathVariable Long id) {
        Optional<User> user = userRepository.findById(id);
        if (user.isPresent()) {
            // NAIVE: N+1 for posts, then N+1 for comments on each post!
            List<?> posts = user.get().getPosts(); // N queries
            for (Object post : posts) {
                // Each post access triggers another query for comments!
            }
            return ResponseEntity.ok(user.get());
        }
        return ResponseEntity.notFound().build();
    }
}